import frappe


def set_visit_case_type(doc, method=None):
    if not doc.patient:
        return

    case_type = frappe.db.get_value(
        "Patient",
        doc.patient,
        "custom_case_type"
    )

    if case_type:
        doc.custom_case_type = case_type
    else:
        doc.custom_case_type = None
