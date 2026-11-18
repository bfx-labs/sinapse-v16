frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
        const grid = frm.fields_dict.items?.grid;
        if (!grid || grid.__batch_order_fix) return;

        const original = grid.setup_visible_columns;

        grid.setup_visible_columns = function () {
            original.call(this);

            const index = this.visible_columns.findIndex(
                ([df]) => df.fieldname === "batch_no"
            );

            if (index < 0) return;

            const batch = this.visible_columns.splice(index, 1)[0];
            const itemIndex = this.visible_columns.findIndex(
                ([df]) => df.fieldname === "item_code"
            );

            if (itemIndex >= 0) {
                this.visible_columns.splice(itemIndex + 1, 0, batch);
            }
        };

        grid.__batch_order_fix = true;
        grid.visible_columns = [];
        grid.refresh();
    }
});
