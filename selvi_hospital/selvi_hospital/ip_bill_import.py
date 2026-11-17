import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_available_source_invoices(inpatient_record, summary_name=None):
    if not inpatient_record:
        frappe.throw("Select an Inpatient Record first.")

    admission = frappe.get_doc("Inpatient Record", inpatient_record)
    patient = admission.get("patient")

    filters = {
        "custom_inpatient_record": inpatient_record,
        "docstatus": 1,
        "is_return": 0,
    }

    invoices = frappe.get_all(
        "Sales Invoice",
        filters=filters,
        fields=[
            "name", "posting_date", "customer",
            "grand_total", "outstanding_amount",
        ],
        order_by="posting_date asc",
    )

    available = []

    for row in invoices:
        linked = frappe.db.sql("""
            SELECT child.parent
            FROM `tabIP Bill Summary Source Invoice` child
            INNER JOIN `tabIP Bill Summary` parent
                ON parent.name = child.parent
            WHERE child.source_invoice = %s
              AND parent.docstatus < 2
        """, (row.name,), as_dict=True)

        # Hide invoices already linked to this summary or another
        # non-cancelled summary.
        if linked:
            continue

        row["patient"] = patient
        available.append(row)

    return available


def validate_source_invoice_import(doc, method=None):
    seen = set()

    for row in doc.get("source_invoices") or []:
        invoice_name = row.get("source_invoice")
        if not invoice_name:
            continue

        if invoice_name in seen:
            frappe.throw(
                "Sales Invoice {} is listed more than once.".format(
                    invoice_name
                )
            )
        seen.add(invoice_name)

        invoice = frappe.db.get_value(
            "Sales Invoice",
            invoice_name,
            [
                "docstatus", "is_return",
                "custom_inpatient_record", "grand_total",
                "posting_date",
            ],
            as_dict=True,
        )

        if not invoice or invoice.docstatus != 1 or invoice.is_return:
            frappe.throw(
                "Only submitted, non-return Sales Invoices can be imported: "
                + invoice_name
            )

        if invoice.custom_inpatient_record != doc.inpatient_record:
            frappe.throw(
                "Sales Invoice {} does not belong to Inpatient Record {}."
                .format(invoice_name, doc.inpatient_record)
            )

        existing = frappe.db.sql(
            """
            SELECT child.parent
            FROM `tabIP Bill Summary Source Invoice` child
            INNER JOIN `tabIP Bill Summary` parent
                ON parent.name = child.parent
            WHERE child.source_invoice = %s
              AND child.parent != %s
              AND parent.docstatus < 2
            LIMIT 1
            """,
            (invoice_name, doc.name or ""),
            as_dict=True,
        )

        if existing:
            frappe.throw(
                "Sales Invoice {} has already been imported into {}."
                .format(invoice_name, existing[0].parent)
            )

        row.invoice_date = invoice.posting_date
        row.invoice_total = flt(invoice.grand_total)


@frappe.whitelist()
def import_source_invoices(summary_name, invoice_names):
    invoice_names = frappe.parse_json(invoice_names) or []

    if not invoice_names:
        frappe.throw("Select at least one Sales Invoice.")

    summary = frappe.get_doc("IP Bill Summary", summary_name)

    if summary.docstatus != 0:
        frappe.throw("Only a draft IP Bill Summary can import invoices.")

    if not summary.inpatient_record:
        frappe.throw("Select an Inpatient Record first.")

    existing_names = {
        row.source_invoice
        for row in (summary.get("source_invoices") or [])
        if row.source_invoice
    }

    for invoice_name in invoice_names:
        if invoice_name in existing_names:
            frappe.throw(f"Sales Invoice {invoice_name} is already imported.")

        invoice = frappe.get_doc("Sales Invoice", invoice_name)

        if invoice.docstatus != 1 or invoice.is_return:
            frappe.throw(
                f"{invoice_name} must be a submitted, non-return Sales Invoice."
            )

        if invoice.get("custom_inpatient_record") != summary.inpatient_record:
            frappe.throw(
                f"{invoice_name} does not belong to the selected Inpatient Record."
            )

        duplicate = frappe.db.sql("""
            SELECT child.parent
            FROM `tabIP Bill Summary Source Invoice` child
            INNER JOIN `tabIP Bill Summary` parent
                ON parent.name = child.parent
            WHERE child.source_invoice = %s
              AND child.parent != %s
              AND parent.docstatus < 2
            LIMIT 1
        """, (invoice_name, summary.name))

        if duplicate:
            frappe.throw(
                f"{invoice_name} is already linked to IP Bill Summary "
                f"{duplicate[0][0]}."
            )

        summary.append("source_invoices", {
            "source_invoice": invoice.name,
            "invoice_date": invoice.posting_date,
            "invoice_total": flt(invoice.grand_total),
        })
        existing_names.add(invoice_name)

    room_total = 0
    medicine_total = 0

    for source_row in summary.get("source_invoices") or []:
        invoice = frappe.get_doc("Sales Invoice", source_row.source_invoice)
        invoice_room_total = 0
        invoice_medicine_total = 0

        for item in invoice.items:
            code = (item.item_code or "").strip().lower()
            name = (item.item_name or "").strip().lower()
            group = (item.item_group or "").strip().lower()
            base_amount = flt(item.net_amount or item.amount)

            tax_amount = 0
            item_tax_rates = item.get("item_tax_rate")

            if item_tax_rates:
                try:
                    item_tax_rates = frappe.parse_json(item_tax_rates) or {}
                except Exception:
                    item_tax_rates = {}

            if isinstance(item_tax_rates, dict) and item_tax_rates:
                for tax in invoice.taxes:
                    rate = flt(item_tax_rates.get(tax.account_head))
                    tax_amount += base_amount * rate / 100
            else:
                tax_amount = flt(item.get("custom_total_gst"))
                if not tax_amount:
                    tax_amount = (
                        flt(item.get("custom_cgst_amount"))
                        + flt(item.get("custom_sgst_amount"))
                    )

            inclusive_amount = base_amount + tax_amount

            is_room = code.startswith("room ") or name.startswith("room ")
            is_medicine = (
                group in {"drug", "tablets", "injections"}
                or any(keyword in group for keyword in (
                    "pharmacy", "medicine", "medication", "capsule",
                    "syrup", "ointment", "consumable"
                ))
            )

            if is_room:
                invoice_room_total += inclusive_amount
            elif is_medicine:
                invoice_medicine_total += inclusive_amount

        source_row.room_amount = round(invoice_room_total, 2)
        source_row.medicines_amount = round(invoice_medicine_total, 2)
        room_total += invoice_room_total
        medicine_total += invoice_medicine_total

    summary.room_charges = round(room_total, 2)
    summary.medicines_consumables = round(medicine_total, 2)

    summary.save()

    return {
        "imported_count": len(invoice_names),
        "source_invoice_count": len(summary.get("source_invoices") or []),
        "room_charges": summary.room_charges,
        "medicines_consumables": summary.medicines_consumables,
        "total_charges": summary.total_charges,
        "grand_total": summary.grand_total,
        "final_payable_amount": summary.final_payable_amount,
    }
