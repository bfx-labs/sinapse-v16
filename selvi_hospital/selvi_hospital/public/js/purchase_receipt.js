frappe.ui.form.on("Purchase Receipt Item", {
    batch_no: async function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (!row.batch_no) {
            return;
        }

        const response = await frappe.db.get_value(
            "Batch",
            row.batch_no,
            ["item", "custom_mrp", "expiry_date"]
        );

        const batch = response.message;

        if (!batch) {
            return;
        }

        if (batch.item !== row.item_code) {
            frappe.msgprint(
                __("Selected Batch does not belong to this Item.")
            );
            return;
        }

        await frappe.model.set_value(
            cdt, cdn, "custom_mrp", batch.custom_mrp || 0
        );

        await frappe.model.set_value(
            cdt, cdn, "custom_expdate", batch.expiry_date || null
        );
    }
});
