import frappe
from frappe.utils import flt


def calculate_purchase_invoice_totals(doc, method=None):
    buy_total = 0
    total_discount = 0
    total_cgst = 0
    total_sgst = 0

    for item in doc.items:
        qty = flt(item.qty)

        buy_rate = flt(item.custom_buy_rate)
        if not buy_rate:
            buy_rate = flt(item.rate)

        item.custom_buy_rate = buy_rate

        mrp = flt(item.custom_mrp)
        item.custom_amount_mrp = flt(qty * mrp, 2)

        buy_amount = flt(qty * buy_rate, 2)
        item.custom_buy_amount = buy_amount

        discount_percent = flt(item.custom_buy_discount_)
        discount_amount = flt(buy_amount * discount_percent / 100, 2)
        taxable_amount = flt(buy_amount - discount_amount, 2)

        cgst_percent = flt(item.custom_cgst)
        sgst_percent = flt(item.custom_sgst)

        item.custom_gst = flt(cgst_percent + sgst_percent, 2)

        cgst_amount = flt(taxable_amount * cgst_percent / 100, 2)
        sgst_amount = flt(taxable_amount * sgst_percent / 100, 2)

        item.custom_buy_net_amount_ = flt(
            taxable_amount + cgst_amount + sgst_amount, 2
        )

        buy_total += buy_amount
        total_discount += discount_amount
        total_cgst += cgst_amount
        total_sgst += sgst_amount

    doc.custom_buy_total = flt(buy_total, 2)
    doc.custom_total_discount = flt(total_discount, 2)
    # Read actual GST amounts from Purchase Taxes and Charges
    invoice_cgst = 0
    invoice_sgst = 0

    for tax in doc.taxes:
        account = (tax.account_head or "").upper()

        if "CGST" in account:
            invoice_cgst += flt(tax.tax_amount)

        elif "SGST" in account:
            invoice_sgst += flt(tax.tax_amount)

    doc.custom_cgst = flt(invoice_cgst, 2)
    doc.custom_sgst = flt(invoice_sgst, 2)
    doc.custom_total_gst = flt(invoice_cgst + invoice_sgst, 2)
    doc.custom_buy_net_total_ = flt(
        buy_total - total_discount + total_cgst + total_sgst, 2
    )
