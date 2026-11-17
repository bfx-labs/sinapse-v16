import frappe
from frappe import _
from frappe.utils import flt, today
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals


TAXABLE_TEMPLATE = "GST - CGST & SGST - SH"
EXEMPT_TEMPLATE = "GST - Not Applicable - SH"
TAXES_TEMPLATE = "GST (5%) - SH"
CGST_ACCOUNT = "Output CGST - SH"
SGST_ACCOUNT = "Output SGST - SH"


def _taxable_template_for_item(source_item):
    # Hospital billing rule: Room 104 is GST-exempt.
    if source_item.item_code == "Room 104":
        return EXEMPT_TEMPLATE

    template = source_item.get("item_tax_template")
    if template:
        return template

    rates = source_item.get("item_tax_rate") or {}
    if isinstance(rates, str):
        rates = frappe.parse_json(rates)

    cgst = flt(rates.get(CGST_ACCOUNT))
    sgst = flt(rates.get(SGST_ACCOUNT))

    if cgst == 2.5 and sgst == 2.5:
        return TAXABLE_TEMPLATE

    if cgst == 0 and sgst == 0:
        return EXEMPT_TEMPLATE

    frappe.throw(
        _("Cannot safely determine GST treatment for item {0} in source invoice {1}.").format(
            source_item.item_code, source_item.parent
        )
    )


@frappe.whitelist()
def create_consolidated_invoice(summary_name):
    summary = frappe.get_doc("IP Bill Summary", summary_name)
    summary.check_permission("write")

    if summary.docstatus != 1:
        frappe.throw(_("Submit the IP Bill Summary before creating its consolidated invoice."))
    if not summary.inpatient_record:
        frappe.throw(_("Select an Inpatient Record first."))
    if not summary.source_invoices:
        frappe.throw(_("Import source invoices first."))

    if summary.consolidated_sales_invoice:
        existing = frappe.get_doc("Sales Invoice", summary.consolidated_sales_invoice)
        if existing.docstatus != 2:
            return {
                "name": existing.name,
                "docstatus": existing.docstatus,
                "grand_total": existing.grand_total,
            }

    sources = []
    seen = set()

    for row in summary.source_invoices:
        if not row.source_invoice or row.source_invoice in seen:
            frappe.throw(_("Source invoices must be selected once each."))
        seen.add(row.source_invoice)

        source = frappe.get_doc("Sales Invoice", row.source_invoice)
        if source.docstatus != 1 or source.is_return:
            frappe.throw(_("{0} must be a submitted, non-return invoice.").format(source.name))
        if source.get("custom_inpatient_record") != summary.inpatient_record:
            frappe.throw(_("{0} belongs to another admission.").format(source.name))

        sources.append(source)

    first = sources[0]
    for source in sources[1:]:
        for field in ("customer", "company", "currency", "debit_to"):
            if source.get(field) != first.get(field):
                frappe.throw(_("Source invoices have different {0} values.").format(field))

    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = first.customer
    invoice.company = first.company
    invoice.currency = first.currency
    invoice.debit_to = first.debit_to
    invoice.conversion_rate = first.conversion_rate or 1
    invoice.posting_date = summary.bill_date or today()
    invoice.due_date = invoice.posting_date
    invoice.custom_inpatient_record = summary.inpatient_record
    # Map patient and practitioner details when the target fields exist.
    invoice_meta = frappe.get_meta('Sales Invoice')
    patient = frappe.get_doc('Patient', summary.patient) if summary.get('patient') else None
    def set_if_field(fieldname, value):
        if invoice_meta.has_field(fieldname) and value is not None:
            invoice.set(fieldname, value)
    set_if_field('patient', summary.get('patient'))
    set_if_field('uhid', summary.get('patient'))
    set_if_field('patient_name', summary.get('patient_name') or (patient.get('patient_name') if patient else None))
    set_if_field('patient_sex', patient.get('sex') if patient else None)
    age = patient.get('patient_age') if patient else None
    if not age and patient and patient.get('dob'):
        age = frappe.utils.date_diff(frappe.utils.today(), patient.dob) // 365
    set_if_field('patient_age', age)
    set_if_field('referring_practitioner', summary.get('referring_practitioner') or first.get('referring_practitioner'))
    set_if_field('doctor_name', summary.get('doctor_name') or first.get('doctor_name'))
    invoice.update_stock = 0
    invoice.taxes_and_charges = None
    invoice.set("taxes", [])
    invoice.remarks = _(
        "Draft consolidation for IP Bill Summary {0}. Source invoices: {1}. "
        "Original invoices and payments have not been changed. "
        "Do not submit until the original-invoice cancellation and payment transition is completed."
    ).format(summary.name, ", ".join(source.name for source in sources))

    # Create one invoice row per non-zero IP Bill Summary category.
    summary_items = [
        ("theatre_charges", "IP-THEATRE-CHG"),
        ("sicu_charges", "IP-SICU-CHG"),
        ("consultant_doctor_charges", "IP-CONSULT-CHG"),
        ("surgeon_charge", "IP-SURGEON-CHG"),
        ("anaesthesia_charge", "IP-ANAESTHESIA-CHG"),
        ("room_charges", "IP-ROOM-CHG"),
        ("assisting_charges", "IP-ASSIST-CHG"),
        ("implant_charges", "IP-IMPLANT-CHG"),
        ("medicines_consumables", "IP-MED-CONS"),
        ("c_arm_charges", "IP-CARM-CHG"),
    ]

    expected_net = 0

    for summary_field, item_code in summary_items:
        amount = flt(summary.get(summary_field))

        if amount <= 0:
            continue

        if not frappe.db.exists("Item", item_code):
            frappe.throw(
                _("Required summary Item {0} does not exist.").format(item_code)
            )

        invoice.append("items", {
            "item_code": item_code,
            "qty": 1,
            "rate": amount,
        })

        expected_net += amount

    discount = flt(summary.get("discount"))

    if discount > 0:
        if discount > expected_net:
            frappe.throw(
                _("Discount cannot exceed the summary subtotal.")
            )

        if not frappe.db.exists("Item", "IP-DISCOUNT"):
            frappe.throw(
                _("Required discount Item IP-DISCOUNT does not exist.")
            )

        discount_account = frappe.get_cached_value(
            "Company",
            first.company,
            "default_income_account"
        )

        if not discount_account:
            frappe.throw(
                _("Configure the default income account for the company.")
            )

        invoice.append("items", {
            "item_code": "IP-DISCOUNT",
            "qty": 1,
            "rate": -discount,
            "income_account": discount_account,
        })

        if invoice_meta.has_field("custom_overall_discount"):
            invoice.custom_overall_discount = discount

        expected_net -= discount

    calculate_taxes_and_totals(invoice).calculate()

    if abs(flt(invoice.net_total) - expected_net) > 0.01:
        frappe.throw(
            _("Summary subtotal mismatch. Expected {0}, calculated {1}. "
              "No invoice was saved.").format(expected_net, invoice.net_total)
        )

    actual_cgst = sum(
        flt(row.tax_amount)
        for row in invoice.taxes
        if row.account_head == CGST_ACCOUNT
    )
    actual_sgst = sum(
        flt(row.tax_amount)
        for row in invoice.taxes
        if row.account_head == SGST_ACCOUNT
    )

    posting_date = summary.bill_date or today()
    invoice.posting_date = posting_date
    invoice.due_date = posting_date
    invoice.payment_terms_template = None
    invoice.set("payment_schedule", [])
    invoice.ignore_default_payment_terms_template = 1
    invoice.insert()

    summary.db_set("consolidated_sales_invoice", invoice.name, update_modified=True)

    return {
        "name": invoice.name,
        "docstatus": invoice.docstatus,
        "net_total": invoice.net_total,
        "cgst": actual_cgst,
        "sgst": actual_sgst,
        "grand_total": invoice.grand_total,
        "rounded_total": invoice.rounded_total,
        "source_invoice_count": len(sources),
        "message": _("Draft created. Original invoices, payments, and stock movements are unchanged."),
    }
