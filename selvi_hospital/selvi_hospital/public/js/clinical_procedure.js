frappe.ui.form.on("Clinical Procedure", {
    refresh(frm) {
        if (
            frm.doc.docstatus === 1 &&
            frm.doc.status === "Completed" &&
            !frm.doc.invoiced
        ) {
            frm.add_custom_button(
                __("Create Sales Invoice"),
                function () {
                    frappe.call({
                        method: "selvi_hospital.api.clinical_procedure.make_sales_invoice",
                        args: {
                            clinical_procedure: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: __("Creating Sales Invoice..."),
                        callback: function (r) {
                            if (r.message) {
                                frappe.msgprint({
                                    title: __("Sales Invoice Created"),
                                    message:
                                        __("Sales Invoice") +
                                        ": <a href='/app/sales-invoice/" +
                                        r.message.sales_invoice +
                                        "'>" +
                                        r.message.sales_invoice +
                                        "</a>",
                                    indicator: "green"
                                });

                                frm.reload_doc();
                            }
                        }
                    });
                },
                __("Actions")
            );
        }
    }
});
