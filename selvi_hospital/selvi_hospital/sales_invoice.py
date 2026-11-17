import frappe
from frappe.utils import flt


def set_sales_invoice_gst(doc, method=None):
    total_cgst = 0
    total_sgst = 0

    # Invoice-level GST
    for tax in doc.taxes:
        account = str(tax.account_head or "").upper()
        amount = flt(tax.tax_amount)

        if "CGST" in account:
            total_cgst += amount

        elif "SGST" in account:
            total_sgst += amount

    doc.custom_cgst = round(total_cgst, 2)
    doc.custom_sgst = round(total_sgst, 2)
    doc.custom_total_gst = round(total_cgst + total_sgst, 2)


def set_sales_invoice_item_gst(doc, method=None):
    for item in doc.items:

        item_cgst = 0
        item_sgst = 0

        for detail in doc.item_wise_tax_details:

            if detail.item_row != item.name:
                continue

            tax_row = next(
                (
                    tax
                    for tax in doc.taxes
                    if tax.name == detail.tax_row
                ),
                None
            )

            if not tax_row:
                continue

            account = str(tax_row.account_head or "").upper()
            amount = flt(detail.amount)

            if "CGST" in account:
                item_cgst += amount

            elif "SGST" in account:
                item_sgst += amount

        frappe.db.set_value(
            "Sales Invoice Item",
            item.name,
            {
                "custom_cgst_amount": round(item_cgst, 2),
                "custom_sgst_amount": round(item_sgst, 2),
                "custom_total_gst": round(item_cgst + item_sgst, 2),
            },
            update_modified=False
        )

def calculate_advance_balance(doc, method=None):
    allocated_advance = sum(
        flt(row.allocated_amount)
        for row in (doc.advances or [])
    )

    patient_payable = flt(doc.patient_payable_amount)

    doc.custom_advance_amount = allocated_advance
    doc.custom_balance_amount = max(
        patient_payable - allocated_advance,
        0
    )

def set_inpatient_practitioner(doc, method=None):
    patient = doc.get("patient")
    if patient:
        patient_data = frappe.db.get_value(
            "Patient", patient, ["custom_age", "sex"], as_dict=True
        )
        if patient_data:
            if patient_data.custom_age and not doc.get("custom_patient_age"):
                doc.custom_patient_age = patient_data.custom_age
            if patient_data.sex and not doc.get("custom_patient_sex"):
                doc.custom_patient_sex = patient_data.sex

    appointment_name = None
    for item in doc.get("items") or []:
        if item.get("reference_dt") == "Patient Appointment" and item.get("reference_dn"):
            appointment_name = item.reference_dn
            break

    if appointment_name:
        appointment_data = frappe.db.get_value(
            "Patient Appointment",
            appointment_name,
            ["practitioner", "practitioner_name", "patient_age", "patient_sex"],
            as_dict=True,
        )
        if appointment_data:
            if appointment_data.practitioner:
                doc.ref_practitioner = appointment_data.practitioner
            if appointment_data.practitioner_name:
                doc.custom_doctor_name_ = appointment_data.practitioner_name
            if appointment_data.patient_age:
                doc.custom_patient_age = appointment_data.patient_age
            if appointment_data.patient_sex:
                doc.custom_patient_sex = appointment_data.patient_sex

    inpatient_name = doc.get("custom_inpatient_record")
    if inpatient_name:
        practitioner = frappe.db.get_value(
            "Inpatient Record", inpatient_name, "primary_practitioner"
        )
        if practitioner:
            doc.ref_practitioner = practitioner
            doc.custom_doctor_name_ = frappe.db.get_value(
                "Healthcare Practitioner", practitioner, "practitioner_name"
            )


@frappe.whitelist()
def get_ip_bill_summary_data(inpatient_record):
    """Return admission and current-room details for a new IP Bill Summary.

    Original Sales Invoices are selected manually through the import dialog.
    This method deliberately does not select invoices or calculate billing.
    """
    if not inpatient_record:
        frappe.throw("Inpatient Record is required.")

    admission = frappe.get_doc("Inpatient Record", inpatient_record)
    admission.check_permission("read")

    occupancies = admission.get("inpatient_occupancies") or []
    active_occupancies = [
        row for row in occupancies
        if not row.get("left") and not row.get("check_out")
    ]

    current_occupancy = (
        max(active_occupancies, key=lambda row: row.get("idx") or 0)
        if active_occupancies else None
    )

    patient = admission.get("patient")
    patient_name = admission.get("patient_name")

    if not patient_name and patient:
        patient_name = frappe.db.get_value(
            "Patient", patient, "patient_name"
        )

    return {
        "patient": patient,
        "patient_name": patient_name,
        "inpatient_record": admission.name,
        "room_no": (
            current_occupancy.get("service_unit")
            if current_occupancy else ""
        ),
    }
