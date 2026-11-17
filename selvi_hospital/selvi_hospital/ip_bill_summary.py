import frappe
from frappe.utils import flt


CHARGE_FIELDS = (
    "theatre_charges",
    "surgeon_charge",
    "assisting_charges",
    "c_arm_charges",
    "room_charges",
    "consultant_doctor_charges",
    "medicines_consumables",
    "sicu_charges",
    "anaesthesia_charge",
    "implant_charges",
)


def calculate_total_charges(doc, method=None):
    """Calculate charges, discount, payable amount, and balance due."""
    doc.total_charges = sum(
        flt(doc.get(fieldname))
        for fieldname in CHARGE_FIELDS
    )

    discount = max(0, flt(doc.get("discount")))
    doc.grand_total = max(0, flt(doc.total_charges) - discount)
    doc.final_payable_amount = doc.grand_total

    amount_paid = max(0, flt(doc.get("amount_paid")))
    doc.balance_due = max(
        0, flt(doc.final_payable_amount) - amount_paid
    )

@frappe.whitelist()
def get_or_create_ip_bill_summary(inpatient_record):
    """Find an existing summary; never create or save one here."""
    if not inpatient_record:
        frappe.throw("Inpatient Record is required.")

    admission = frappe.get_doc("Inpatient Record", inpatient_record)
    admission.check_permission("read")

    existing = frappe.get_all(
        "IP Bill Summary",
        filters={"inpatient_record": admission.name},
        fields=["name"],
        order_by="creation asc",
        limit=1,
    )

    return existing[0].name if existing else None


def validate_before_submit(doc, method=None):
    """Validate IP Bill Summary before final submission."""
    if not doc.patient:
        frappe.throw("Please select a Patient before submitting.")

    if not doc.inpatient_record:
        frappe.throw("Please select an Inpatient Record before submitting.")

    if not doc.bill_date:
        frappe.throw("Please set the Bill Date before submitting.")

    duplicate = frappe.db.exists(
        "IP Bill Summary",
        {
            "inpatient_record": doc.inpatient_record,
            "docstatus": 1,
            "name": ["!=", doc.name],
        },
    )

    if duplicate:
        frappe.throw(
            f"Admission {doc.inpatient_record} already has a "
            f"submitted IP Bill Summary: {duplicate}"
        )
def sync_payment_details(summary_name):
    """Synchronize IP Bill Summary payment status with its consolidated invoice."""
    summary = frappe.get_doc("IP Bill Summary", summary_name)

    # Draft summaries must always show Draft payment status.
    if summary.docstatus == 0:
        frappe.db.set_value(
            "IP Bill Summary",
            summary.name,
            "custom_payment_status",
            "Draft",
            update_modified=False,
        )
        return

    if summary.docstatus == 2:
        return

    invoice_name = summary.get("consolidated_sales_invoice")

    # Submitted summary without a submitted consolidated invoice.
    if not invoice_name or not frappe.db.get_value(
        "Sales Invoice", invoice_name, "docstatus"
    ) == 1:
        amount_due = max(0, flt(summary.get("final_payable_amount")))

        frappe.db.set_value(
            "IP Bill Summary",
            summary.name,
            {
                "amount_paid": 0,
                "balance_due": amount_due,
                "custom_payment_status": "Unpaid",
            },
            update_modified=False,
        )
        return

    invoice = frappe.get_doc("Sales Invoice", invoice_name)

    grand_total = max(0, flt(invoice.grand_total))
    outstanding = max(0, flt(invoice.outstanding_amount))
    amount_paid = max(0, grand_total - outstanding)

    if outstanding <= 0:
        payment_status = "Paid"
    elif amount_paid > 0:
        payment_status = "Partly Paid"
    else:
        payment_status = "Unpaid"

    frappe.db.set_value(
        "IP Bill Summary",
        summary.name,
        {
            "amount_paid": amount_paid,
            "balance_due": outstanding,
            "custom_payment_status": payment_status,
        },
        update_modified=False,
    )


def sync_summaries_for_invoice(invoice_name):
    """Update all IP Bill Summaries linked to a Sales Invoice."""
    if not invoice_name:
        return

    summaries = frappe.get_all(
        "IP Bill Summary",
        filters={"consolidated_sales_invoice": invoice_name},
        pluck="name",
    )

    for summary_name in summaries:
        sync_payment_details(summary_name)


def sync_from_payment_entry(doc, method=None):
    """Refresh summaries affected by Payment Entry submission/cancellation."""
    for reference in doc.get("references") or []:
        if reference.reference_doctype == "Sales Invoice":
            sync_summaries_for_invoice(reference.reference_name)


def sync_from_sales_invoice(doc, method=None):
    """Refresh summaries when a Sales Invoice changes."""
    sync_summaries_for_invoice(doc.name)


def sync_sales_invoice_link(doc, method=None):
    """Maintain the reverse link from Sales Invoice to IP Bill Summary."""
    invoice_name = doc.get("consolidated_sales_invoice")

    previous = doc.get_doc_before_save()
    old_invoice = (
        previous.get("consolidated_sales_invoice")
        if previous else None
    )

    if old_invoice and old_invoice != invoice_name:
        if frappe.db.get_value(
            "Sales Invoice", old_invoice, "custom_ip_bill_summary"
        ) == doc.name:
            frappe.db.set_value(
                "Sales Invoice",
                old_invoice,
                "custom_ip_bill_summary",
                None,
                update_modified=False,
            )

    if invoice_name:
        frappe.db.set_value(
            "Sales Invoice",
            invoice_name,
            "custom_ip_bill_summary",
            doc.name,
            update_modified=False,
        )
