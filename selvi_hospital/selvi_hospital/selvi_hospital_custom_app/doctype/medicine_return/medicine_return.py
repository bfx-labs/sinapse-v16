
import frappe
from frappe.model.document import Document
from frappe.utils import flt


class MedicineReturn(Document):

    def validate(self):
        self.validate_company()
        self.calculate_refund()

    def validate_company(self):
        if self.company != "Selvi Hospital":
            frappe.throw("Medicine Return is configured for Selvi Hospital.")

        required_records = [
            ("Warehouse", "Stores - SH"),
            ("Account", "Patient Medicine Refunds - SH"),
            ("Account", "Stock Adjustment - SH"),
            ("Cost Center", "Main - SH")
        ]

        for doctype, name in required_records:
            if not frappe.db.exists(doctype, name):
                frappe.throw(f"{doctype} {name} does not exist.")

        account_type = frappe.db.get_value(
            "Account", self.refund_account, "account_type"
        )
        account_company = frappe.db.get_value(
            "Account", self.refund_account, "company"
        )

        expected_type = "Cash" if self.refund_mode == "Cash" else "Bank"

        if account_company != self.company:
            frappe.throw("Refund account must belong to Selvi Hospital.")

        if account_type != expected_type:
            frappe.throw(
                f"{self.refund_mode} refund requires a {expected_type} account."
            )

    def calculate_refund(self):
        if not self.items:
            frappe.throw("Please add at least one returned medicine.")

        total = 0

        for row in self.items:
            if flt(row.qty) <= 0:
                frappe.throw(f"Invalid return quantity for {row.item_code}.")

            item = frappe.get_doc("Item", row.item_code)

            if not item.is_stock_item:
                frappe.throw(f"{row.item_code} is not a stock item.")

            if item.has_batch_no:
                if not row.batch_no:
                    frappe.throw(f"Select a batch for {row.item_code}.")

                batch = frappe.db.get_value(
                    "Batch",
                    row.batch_no,
                    ["item", "expiry_date", "custom_mrp"],
                    as_dict=True
                )

                if not batch or batch.item != row.item_code:
                    frappe.throw(
                        f"Invalid batch {row.batch_no} for {row.item_code}."
                    )

                row.expiry_date = batch.expiry_date

                if not flt(row.mrp):
                    row.mrp = flt(batch.custom_mrp)

            elif row.batch_no:
                frappe.throw(
                    f"{row.item_code} does not require a batch number."
                )

            if flt(row.mrp) <= 0:
                frappe.throw(f"Enter a valid MRP for {row.item_code}.")

            bin_rate = frappe.db.get_value(
                "Bin",
                {
                    "item_code": row.item_code,
                    "warehouse": "Stores - SH"
                },
                "valuation_rate"
            )

            valuation_rate = flt(bin_rate) or flt(item.valuation_rate)

            if valuation_rate <= 0:
                frappe.throw(
                    f"No valuation rate found for {row.item_code}."
                )

            row.valuation_rate = valuation_rate
            row.refund_amount = flt(row.mrp) * flt(row.qty)
            total += flt(row.refund_amount)

        self.total_refund = total

    def on_submit(self):
        self.create_stock_entry()
        self.create_refund_journal_entry()

    def create_stock_entry(self):
        existing = frappe.db.get_value(
            "Stock Entry",
            {"remarks": f"Medicine Return: {self.name}", "docstatus": ["!=", 2]},
            "name"
        )
        if existing:
            self.db_set("stock_entry", existing, update_modified=False)
            return

        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Receipt"
        stock_entry.company = self.company
        stock_entry.posting_date = self.return_date
        stock_entry.set_posting_time = 1
        stock_entry.custom_b_no = 0
        stock_entry.remarks = f"Medicine Return: {self.name}"

        for row in self.items:
            item = frappe.get_doc("Item", row.item_code)

            stock_entry.append("items", {
                "item_code": row.item_code,
                "qty": row.qty,
                "uom": item.stock_uom,
                "conversion_factor": 1,
                "basic_rate": row.valuation_rate,
                "custom_total_amount": row.refund_amount,
                "t_warehouse": "Stores - SH",
                "batch_no": row.batch_no,
                "use_serial_batch_fields": 1,
                "expense_account": "Stock Adjustment - SH",
                "cost_center": "Main - SH"
            })

        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()

        self.db_set(
            "stock_entry",
            stock_entry.name,
            update_modified=False
        )

    def create_refund_journal_entry(self):
        existing = frappe.db.get_value(
            "Journal Entry",
            {"user_remark": f"Medicine refund: {self.name}", "docstatus": ["!=", 2]},
            "name"
        )
        if existing:
            self.db_set("journal_entry", existing, update_modified=False)
            return

        journal = frappe.new_doc("Journal Entry")
        journal.voucher_type = "Journal Entry"
        journal.company = self.company
        journal.posting_date = self.return_date
        journal.user_remark = f"Medicine refund: {self.name}"

        journal.append("accounts", {
            "account": "Patient Medicine Refunds - SH",
            "debit_in_account_currency": self.total_refund,
            "cost_center": "Main - SH"
        })

        journal.append("accounts", {
            "account": self.refund_account,
            "credit_in_account_currency": self.total_refund,
            "cost_center": "Main - SH"
        })

        journal.insert(ignore_permissions=True)
        journal.submit()

        self.db_set(
            "journal_entry",
            journal.name,
            update_modified=False
        )

    def on_cancel(self):
        if self.journal_entry:
            journal = frappe.get_doc("Journal Entry", self.journal_entry)
            if journal.docstatus == 1:
                journal.cancel()

        if self.stock_entry:
            stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
            if stock_entry.docstatus == 1:
                stock_entry.cancel()


@frappe.whitelist()
def get_medicine_return_batches(item_code):
    if not item_code:
        return []

    batches = frappe.db.sql("""
        SELECT
            b.name,
            b.batch_id,
            b.item_name,
            b.expiry_date,
            b.custom_mrp,
            COALESCE(SUM(sbe.qty), 0) AS available_qty
        FROM `tabBatch` b
        LEFT JOIN `tabSerial and Batch Entry` sbe
            ON sbe.batch_no = b.name
            AND sbe.item_code = b.item
            AND sbe.warehouse = 'Stores - SH'
            AND sbe.is_cancelled = 0
            AND sbe.docstatus = 1
        WHERE b.item = %s
          AND b.disabled = 0
        GROUP BY
            b.name, b.batch_id, b.item_name,
            b.expiry_date, b.custom_mrp
        HAVING available_qty > 0
        ORDER BY b.expiry_date ASC
    """, item_code, as_dict=True)

    return batches


# Event handlers for the Medicine Return Custom DocType.
# Custom DocTypes use the standard Frappe Document controller.

def medicine_return_validate(doc, method=None):
    MedicineReturn.validate_company(doc)
    MedicineReturn.calculate_refund(doc)


def medicine_return_on_submit(doc, method=None):
    # Prevent duplicate generated entries.
    if not doc.stock_entry:
        MedicineReturn.create_stock_entry(doc)

    if not doc.journal_entry:
        MedicineReturn.create_refund_journal_entry(doc)


def medicine_return_on_cancel(doc, method=None):
    MedicineReturn.on_cancel(doc)
