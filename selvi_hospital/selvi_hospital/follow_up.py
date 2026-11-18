import frappe
from frappe.utils import getdate


def sync_patient_follow_up(doc, method=None):
    if not doc.patient:
        return

    patient = frappe.get_doc("Patient", doc.patient)

    existing_row = None

    for row in patient.get("custom_follow_up_date") or []:
        if row.custom_patient_encounter == doc.name:
            existing_row = row
            break

    follow_up_date = doc.custom_follow_up_date

    if not follow_up_date:
        if existing_row:
            patient.remove(existing_row)
            patient.save(ignore_permissions=True)
        return

    interval = doc.custom_follow_up_interval

    interval_values = {
        "Days": doc.custom_follow_up_days,
        "Weeks": doc.custom_follow_up_weeks,
        "Months": doc.custom_follow_up_months,
    }

    interval_options = {
        "Days": "Daily",
        "Weeks": "Weekly",
        "Months": "Monthly",
    }

    days = interval_values.get(interval)

    if not interval or not days or days <= 0:
        frappe.throw(
            "Please select a valid Follow-up Interval and enter its value."
        )

    if existing_row:
        row = existing_row
    else:
        row = patient.append("custom_follow_up_date", {})

    row.visited_date = doc.encounter_date
    row.days = days
    row.intervals = interval_options[interval]
    row.next_visit_date = getdate(follow_up_date)
    row.status = "Not Visited"
    row.custom_patient_encounter = doc.name

    patient.save(ignore_permissions=True)
