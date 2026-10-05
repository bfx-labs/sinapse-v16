import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def make_sales_invoice(clinical_procedure):
    """
    Create a Sales Invoice for a completed Clinical Procedure.
    """

    cp = frappe.get_doc("Clinical Procedure", clinical_procedure)

    # Prevent duplicate invoices
    if cp.invoiced:
        frappe.throw(
            _("Clinical Procedure {0} is already invoiced.").format(cp.name)
        )

    # Procedure must be completed
    if cp.status != "Completed":
        frappe.throw(
            _("Clinical Procedure {0} must be completed before invoicing.").format(
                cp.name
            )
        )

    # Get patient customer
    customer = frappe.db.get_value(
        "Patient",
        cp.patient,
        "customer"
    )

    if not customer:
        frappe.throw(
            _("Please set a Customer for Patient {0}.").format(cp.patient)
        )

    # Get procedure template
    template = frappe.get_doc(
        "Clinical Procedure Template",
        cp.procedure_template
    )

    if not template.is_billable:
        frappe.throw(
            _("Clinical Procedure Template {0} is not billable.").format(
                template.name
            )
        )

    if not template.item:
        frappe.throw(
            _("No Item is configured for Clinical Procedure Template {0}.").format(
                template.name
            )
        )

    # Determine rate
    rate = flt(template.rate)

    if not rate:
        rate = flt(
            frappe.db.get_value(
                "Item Price",
                {
                    "item_code": template.item,
                    "selling": 1,
                    "price_list": "Standard Selling",
                },
                "price_list_rate",
            )
        )

    if not rate:
        frappe.throw(
            _("No selling rate found for Item {0}.").format(template.item)
        )

    # Create Sales Invoice
    invoice = frappe.new_doc("Sales Invoice")

    invoice.company = cp.company
    invoice.customer = customer
    invoice.patient = cp.patient

    # Existing custom fields in your Sales Invoice
    if hasattr(invoice, "ref_practitioner"):
        invoice.ref_practitioner = cp.practitioner

    if hasattr(invoice, "custom_doctor_name_"):
        invoice.custom_doctor_name_ = frappe.db.get_value(
            "Healthcare Practitioner",
            cp.practitioner,
            "practitioner_name"
        )

    # Link the inpatient record when available
    if cp.inpatient_record and hasattr(invoice, "custom_inpatient_record"):
        invoice.custom_inpatient_record = cp.inpatient_record

    # Add procedure item
    item = invoice.append("items", {})
    item.item_code = template.item
    item.qty = 1
    item.rate = rate
    item.description = template.custom_item_name or template.description or template.name

    # Reference the Clinical Procedure
    item.reference_dt = "Clinical Procedure"
    item.reference_dn = cp.name

    invoice.set_missing_values()

    invoice.insert(ignore_permissions=True)

    # Mark Clinical Procedure as invoiced
    frappe.db.set_value(
        "Clinical Procedure",
        cp.name,
        "invoiced",
        1,
        update_modified=True
    )   

    frappe.db.commit()

    return {
        "sales_invoice": invoice.name,
        "clinical_procedure": cp.name,
        "patient": cp.patient,
        "item": template.item,
        "amount": invoice.grand_total,
    }
