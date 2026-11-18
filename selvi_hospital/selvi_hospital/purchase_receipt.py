import frappe


def get_row_batch_numbers(row):
    batch_nos = set()

    if row.get("batch_no"):
        batch_nos.add(row.batch_no)

    if row.get("serial_and_batch_bundle"):
        bundle = frappe.get_doc(
            "Serial and Batch Bundle",
            row.serial_and_batch_bundle
        )

        for entry in bundle.entries:
            if entry.batch_no:
                batch_nos.add(entry.batch_no)

    return batch_nos


def fetch_batch_mrp_expiry(doc, method=None):
    """Fetch MRP and expiry from the selected Batch."""

    for row in doc.items:
        batch_nos = get_row_batch_numbers(row)

        if len(batch_nos) != 1:
            continue

        batch_no = next(iter(batch_nos))

        batch = frappe.db.get_value(
            "Batch",
            batch_no,
            ["item", "custom_mrp", "expiry_date"],
            as_dict=True
        )

        if not batch:
            continue

        if batch.item != row.item_code:
            frappe.throw(
                f"Batch {batch_no} does not belong to Item {row.item_code}"
            )

        row.custom_mrp = batch.custom_mrp or 0
        row.custom_expdate = batch.expiry_date


def fetch_sales_invoice_batch_mrp_expiry(doc, method=None):
    """Fetch MRP and expiry from the selected Batch into Sales Invoice."""

    for row in doc.items:
        batch_nos = get_row_batch_numbers(row)

        if len(batch_nos) != 1:
            continue

        batch_no = next(iter(batch_nos))

        batch = frappe.db.get_value(
            "Batch",
            batch_no,
            ["item", "custom_mrp", "expiry_date"],
            as_dict=True
        )

        if not batch:
            continue

        if batch.item != row.item_code:
            frappe.throw(
                f"Batch {batch_no} does not belong to Item {row.item_code}"
            )

        row.rate = batch.custom_mrp or 0
        row.custom_expiry_date = batch.expiry_date


def apply_op_ip_discount(doc, method=None):
    """Apply 5% discount for OP and no discount for normal IP invoices."""

    # Consolidated IP invoices use the discount from IP Bill Summary.
    if doc.get("custom_ip_bill_summary"):
        return

    is_ip = bool(doc.get("custom_inpatient_record"))
    discount = 0 if is_ip else 5

    changed = False

    for row in doc.items:
        if row.discount_percentage != discount:
            row.discount_percentage = discount
            changed = True

    if is_ip:
        for field in (
            "discount_amount",
            "additional_discount_percentage",
            "custom_overall_discount",
        ):
            if doc.get(field):
                doc.set(field, 0)
                changed = True

    if changed:
        doc.calculate_taxes_and_totals()



def update_generated_batch_details(doc, method=None):
    """Sync generated Batch ID and MRP after Purchase Receipt submission."""

    submitted_doc = frappe.get_doc("Purchase Receipt", doc.name)
    affected_items = set()

    for row in submitted_doc.items:
        batch_nos = get_row_batch_numbers(row)

        if len(batch_nos) != 1:
            continue

        batch_no = next(iter(batch_nos))

        batch_item = frappe.db.get_value(
            "Batch", batch_no, "item"
        )

        if batch_item != row.item_code:
            frappe.throw(
                f"Batch {batch_no} does not belong to Item {row.item_code}"
            )

        frappe.db.set_value(
            "Purchase Receipt Item",
            row.name,
            "batch_no",
            batch_no,
            update_modified=False
        )

        frappe.db.set_value(
            "Batch",
            batch_no,
            "custom_mrp",
            row.custom_mrp or 0,
            update_modified=False
        )

        affected_items.add(row.item_code)

    # Refresh Item Available Batches after Batch MRP and stock are updated.
    for item_code in affected_items:
        sync_item_batches(item_code)


def sync_item_batches(item_code):
    """Rebuild the Item's Available Batches table from Batch records."""
    if not item_code or not frappe.db.exists("Item", item_code):
        return

    batches = frappe.get_all(
        "Batch",
        filters={"item": item_code},
        fields=[
            "name",
            "custom_mrp",
            "manufacturing_date",
            "expiry_date",
            "batch_qty"
        ],
        order_by="creation desc"
    )

    item = frappe.get_doc("Item", item_code)
    item.set("custom_item_batches", [])

    for batch in batches:
        item.append("custom_item_batches", {
            "batch": batch.name,
            "custom_mrp": batch.custom_mrp,
            "manufacturing_date": batch.manufacturing_date,
            "expiry_date": batch.expiry_date,
            "batch_qty": batch.batch_qty
        })

    item.save(ignore_permissions=True)


def sync_item_batches_on_update(doc, method=None):
    """Refresh the Item batch table after a Batch is saved."""
    sync_item_batches(doc.item)


def set_item_shelf_life_from_group(doc, method=None):
    """Apply Item Group shelf-life default when Item shelf life is empty."""
    if doc.get("shelf_life_in_days"):
        return

    item_group = doc.get("item_group")
    if not item_group:
        return

    default_days = frappe.db.get_value(
        "Item Group",
        item_group,
        "custom_shelf_life_in_days"
    )

    if default_days:
        doc.shelf_life_in_days = default_days


def set_batch_expiry_from_shelf_life(doc, method=None):
    """Calculate Batch expiry when no actual expiry date is supplied."""
    if doc.get("expiry_date") or not doc.get("manufacturing_date"):
        return

    if not doc.get("item"):
        return

    shelf_life = frappe.db.get_value(
        "Item",
        doc.item,
        "shelf_life_in_days"
    )

    if shelf_life:
        doc.expiry_date = frappe.utils.add_days(
            doc.manufacturing_date,
            shelf_life
        )


def set_item_gst_from_tax_template(doc, method=None):
    """Set Item CGST and SGST percentages from the selected tax template."""

    target_template = "GST - CGST & SGST - SH"

    selected = any(
        row.item_tax_template == target_template
        for row in (doc.get("taxes") or [])
    )

    if not selected:
        return

    template = frappe.get_doc("Item Tax Template", target_template)

    cgst = 0
    sgst = 0

    for row in template.taxes:
        tax_type = (row.tax_type or "").upper()

        if "CGST" in tax_type:
            cgst = row.tax_rate or 0

        elif "SGST" in tax_type:
            sgst = row.tax_rate or 0

    doc.custom_cgst_ = cgst
    doc.custom_sgst_ = sgst


def set_item_dosage_form_from_group(doc, method=None):
    """Set default Dosage Form from Item Group when not already selected."""

    if doc.get("custom_dosage_form"):
        return

    dosage_mapping = {
        "Tablets": "Tablet",
        "Syrups": "Syrups",
        "Drops": "Drops",
        "Ointment": "Oinment",
        "Injections": "Injection",
        "IV Fluid": "Consumable",
    }

    dosage_form = dosage_mapping.get(doc.get("item_group"))

    if dosage_form and frappe.db.exists("Dosage Form", dosage_form):
        doc.custom_dosage_form = dosage_form

