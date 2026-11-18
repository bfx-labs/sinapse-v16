frappe.ui.form.on("Inpatient Record", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.name) return;

        frm.add_custom_button(__("Create IP Bill Summary"), () => {
            frappe.call({
                method: "selvi_hospital.ip_bill_summary.get_or_create_ip_bill_summary",
                args: {
                    inpatient_record: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Checking IP Bill Summary..."),
                callback(r) {
                    if (r.message) {
                        // Existing saved summary: open it.
                        frappe.set_route("Form", "IP Bill Summary", r.message);
                        return;
                    }

                    // No saved summary: open a NEW, UNSAVED form.
                    frappe.new_doc("IP Bill Summary", {
                        patient: frm.doc.patient,
                        patient_name: frm.doc.patient_name,
                        inpatient_record: frm.doc.name,
                        room_no: frm.doc.inpatient_occupancy,
                        bill_date: frappe.datetime.get_today()
                    });
                }
            });
        }, __("Billing"));
    }
});
