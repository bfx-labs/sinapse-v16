frappe.ui.form.on("Patient Encounter", {
    refresh(frm) {
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frm.add_custom_button(__("Create Vital Signs"), function () {
                if (!frm.doc.patient) {
                    frappe.msgprint(__("Please select a Patient first."));
                    return;
                }

                frappe.new_doc("Vital Signs", {
                    patient: frm.doc.patient,
                    encounter: frm.doc.name
                });
            }, __("Actions"));
        }
    }
});
