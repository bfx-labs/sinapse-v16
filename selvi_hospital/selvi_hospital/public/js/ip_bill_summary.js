frappe.ui.form.on("IP Bill Summary", {
    refresh(frm) {

        // Keep the import action available on draft and unsaved summaries.
        frm.remove_custom_button(__("Import Source Invoices"), __("Billing"));

        if (frm.doc.docstatus === 0 || frm.is_new()) {
            frm.add_custom_button(
                __("Import Source Invoices"),
                () => {
                    if (typeof window.open_source_invoice_dialog === "function") {
                        window.open_source_invoice_dialog(frm);
                    } else {
                        frappe.msgprint(__("The invoice import dialog did not load. Refresh the page and try again."));
                    }
                }
            );
        }
        if (
            frm.doc.docstatus === 1 &&
            !frm.doc.consolidated_sales_invoice
        ) {
            frm.remove_custom_button(__("Create Consolidated Sales Invoice"));
            frm.page.clear_primary_action();
            frm.page.set_primary_action(
                __("Create Consolidated Sales Invoice"),
                async () => {
                    frappe.confirm(
                        __("Create a draft consolidated Sales Invoice?"),
                        async () => {
                            const response = await frappe.call({
                                method: "selvi_hospital.ip_bill_consolidation.create_consolidated_invoice",
                                args: { summary_name: frm.doc.name },
                                freeze: true,
                                freeze_message: __("Creating consolidated draft invoice...")
                            });

                            if (response.message && response.message.name) {
                                await frm.reload_doc();
                                frappe.set_route(
                                    "Form",
                                    "Sales Invoice",
                                    response.message.name
                                );
                            }
                        }
                    );
                }
            );
        } else {
            frm.remove_custom_button(__("Create Consolidated Sales Invoice"));

            // Restore Submit action for saved draft documents.
            if (frm.doc.docstatus === 0 && !frm.is_new()) {
                frm.page.set_primary_action(
                    __("Submit"),
                    () => frm.save("Submit")
                );
            } else if (frm.doc.docstatus === 1) {
                frm.page.clear_primary_action();
            }
        }


        // Restore the existing Submit button for saved draft documents.
        if (
            frm.doc.docstatus === 0 &&
            !frm.is_new() &&
            frm.perm?.[0]?.submit
        ) {
            const showSubmit = () => {
                frm.page.wrapper
                    .find("button.primary-action")
                    .filter(function () {
                        return this.textContent.trim() === __("Submit");
                    })
                    .removeClass("hide")
                    .show();
            };

            showSubmit();
            setTimeout(showSubmit, 100);
        }

        // Ensure the consolidation action is visible after submission.
        if (
            frm.doc.docstatus === 1 &&
            !frm.doc.consolidated_sales_invoice
        ) {
            frm.page.wrapper
                .find("button.primary-action")
                .filter(function () {
                    return this.textContent.trim() ===
                        __("Create Consolidated Sales Invoice");
                })
                .removeClass("hide")
                .show();
        }

        // Related record navigation links
        const relatedLinks = [
            ["Sales Invoice", "Sales Invoice", frm.doc.consolidated_sales_invoice],
            ["Inpatient Record", "Inpatient Record", frm.doc.inpatient_record],
            ["Patient", "Patient", frm.doc.patient]
        ];

        const htmlField = frm.fields_dict.related_record_links;
        if (htmlField) {
            const html = relatedLinks
                .filter(([label, doctype, name]) => Boolean(name))
                .map(([label, doctype, name]) => {
                    const route = `/app/${frappe.router.slug(doctype)}/${encodeURIComponent(name)}`;
                    return `<div class="mb-2"><a href="${route}">${frappe.utils.escape_html(label)}: ${frappe.utils.escape_html(name)}</a></div>`;
                }).join("");

            htmlField.$wrapper.html(
                `<div class="small text-muted mb-2">Related Records</div>${html || __("No related records linked.")}`
            );
        }


        console.log("[IP Connections] refresh handler reached", frm.doc.name);
        // Add Connections dashboard section after Frappe dashboard refresh.
        setTimeout(() => {
            console.log("[IP Connections] dashboard check", {
                exists: !!frm.dashboard,
                isNew: frm.is_new(),
                addSection: typeof frm.dashboard?.add_section
            });

            if (!frm.dashboard || frm.is_new()) return;

            const connections = [
                {
                    label: __("Sales Invoice"),
                    doctype: "Sales Invoice",
                    name: frm.doc.consolidated_sales_invoice
                },
                {
                    label: __("Inpatient Record"),
                    doctype: "Inpatient Record",
                    name: frm.doc.inpatient_record
                },
                {
                    label: __("Patient"),
                    doctype: "Patient",
                    name: frm.doc.patient
                }
            ].filter(item => item.name);

            const html = connections.length
                ? connections.map(item => {
                    const route = `/app/${frappe.router.slug(item.doctype)}/${encodeURIComponent(item.name)}`;
                    return `
                        <div class="mb-3">
                            <a href="${route}">
                                <span class="text-muted">${frappe.utils.escape_html(item.label)}</span>
                                <br>
                                <strong>${frappe.utils.escape_html(item.name)}</strong>
                            </a>
                        </div>
                    `;
                }).join("")
                : `<div class="text-muted">${__("No connected documents.")}</div>`;

            frm.dashboard.add_section(html, __("Connections"), "custom");
        }, 0);

        console.log("[IP Bill Summary] refresh executed", frm.doc.name);

        ["patient", "inpatient_record", "patient_name"].forEach(fieldname => {
            const field = frm.fields_dict[fieldname];
            const section = field?.$wrapper?.closest(".form-section");
            if (section?.length) {
                section.removeClass("hide").show();
            }
        });

        if (frm.doc.name && frm.doc.consolidated_sales_invoice) {
            frm.add_custom_button(
                __("Open Sales Invoice"),
                () => frappe.set_route(
                    "Form",
                    "Sales Invoice",
                    frm.doc.consolidated_sales_invoice
                ),
                __("Billing")
            );
        }

        // Never auto-populate fields on submitted summaries.
        // frm.set_value() can otherwise mark them as unsaved.
        if (
            frm.doc.docstatus === 0 &&
            frm.doc.__islocal &&
            frm.doc.inpatient_record &&
            !frm.__ip_summary_loaded &&
            !frm.__ip_summary_loading
        ) {
            load_ip_bill_summary(frm);
        }
    },

    inpatient_record(frm) {
        if (frm.doc.inpatient_record) {
            frm.__ip_summary_loaded = false;
            load_ip_bill_summary(frm);
        }
    },

    consolidated_sales_invoice(frm) {
        if (frm.__ip_summary_setting_invoice) return;

        if (frm.doc.consolidated_sales_invoice) {
            frm.__ip_summary_loaded = false;
            load_ip_bill_summary(frm);
        }
    },

    discount(frm) {
        calculate_final_payable_amount(frm);
    },

    grand_total(frm) {
        if (frm.__ip_bill_calculating) return;
        calculate_final_payable_amount(frm);
    }
});

async function calculate_final_payable_amount(frm) {
    if (frm.doc.docstatus !== 0 || frm.__ip_bill_calculating) return;

    frm.__ip_bill_calculating = true;

    try {
        const totalCharges = Math.max(0, flt(frm.doc.total_charges));
        const discount = Math.max(0, flt(frm.doc.discount));
        const grandTotal = Math.max(0, totalCharges - discount);
        const amountPaid = Math.max(0, flt(frm.doc.amount_paid));
        const balanceDue = Math.max(0, grandTotal - amountPaid);

        // Update the draft's in-memory values immediately.
        frm.doc.grand_total = grandTotal;
        frm.doc.final_payable_amount = grandTotal;
        frm.doc.balance_due = balanceDue;

        // Refresh displayed fields without recursively firing field events.
        frm.refresh_field("grand_total");
        frm.refresh_field("final_payable_amount");
        frm.refresh_field("balance_due");

        // Mark the form as changed so the calculated values can be saved.
        frm.dirty();
    } finally {
        frm.__ip_bill_calculating = false;
    }
}

async function load_ip_bill_summary(frm) {
    // Never auto-update a submitted IP Bill Summary.
    if (frm.doc.docstatus !== 0) return;

    if (!frm.doc.inpatient_record || frm.__ip_summary_loading) return;

    frm.__ip_summary_loading = true;
    const requestId = (frm.__ip_summary_request_id || 0) + 1;
    frm.__ip_summary_request_id = requestId;

    const isCurrentRequest = () =>
        frm.__ip_summary_request_id === requestId;

    try {
        const invoiceFromRoute = frappe.route_options?.source_invoice;

        let response = await frappe.call({
            method: "selvi_hospital.sales_invoice.get_ip_bill_summary_data",
            args: {
                inpatient_record: frm.doc.inpatient_record,
                source_invoice: frm.doc.consolidated_sales_invoice || invoiceFromRoute || "",
                consolidated_sales_invoice:
                    frm.doc.consolidated_sales_invoice || invoiceFromRoute || ""
            }
        });

        if (!isCurrentRequest()) return;

        let data = response.message;
        if (!data) throw new Error("The summary API returned no data.");

        // Automatically select the invoice when exactly one is linked.
        const selectedInvoice =
            frm.doc.consolidated_sales_invoice ||
            invoiceFromRoute ||
            (data.invoices?.length === 1 ? data.invoices[0].name : "");

        if (selectedInvoice) {
            if (frm.doc.consolidated_sales_invoice !== selectedInvoice) {
                frm.__ip_summary_setting_invoice = true;
                try {
                    await frm.set_value(
                        "consolidated_sales_invoice",
                        selectedInvoice
                    );
                } finally {
                    frm.__ip_summary_setting_invoice = false;
                }
            }

            response = await frappe.call({
                method: "selvi_hospital.sales_invoice.get_ip_bill_summary_data",
                args: {
                    inpatient_record: frm.doc.inpatient_record,
                    source_invoice: selectedInvoice,
                    consolidated_sales_invoice: selectedInvoice
                }
            });

            if (!isCurrentRequest()) return;

            data = response.message;
            if (!data) throw new Error("The selected invoice returned no data.");
        }

        await frm.set_value("patient", data.patient || "");
        await frm.set_value("patient_name", data.patient_name || "");
        await frm.set_value("inpatient_record", data.inpatient_record || "");
        // Preserve the bill date; do not overwrite it from the API response.
        await frm.set_value("room_no", data.room_no || "");

        if (!isCurrentRequest()) return;

        // Source Sales Invoices table was removed from IP Bill Summary.

        await frm.set_value(
            "room_charges",
            flt(data.room_charges)
        );
        await frm.set_value(
            "medicines_consumables",
            flt(data.medicines_consumables)
        );
        // GST is intentionally excluded from Grand Total for now.
        await frm.set_value("amount_paid", flt(data.amount_paid));
        await frm.set_value("balance_due", flt(data.balance_due));

        if (!isCurrentRequest()) return;

        const chargeFields = [
            "theatre_charges",
            "sicu_charges",
            "surgeon_charge",
            "anaesthesia_charge",
            "assisting_charges",
            "implant_charges",
            "c_arm_charges",
            "room_charges",
            "consultant_doctor_charges",
            "medicines_consumables"
        ];

        const totalCharges = chargeFields.reduce(
            (total, field) => total + flt(frm.doc[field]),
            0
        );

        await frm.set_value("total_charges", totalCharges);
        await calculate_final_payable_amount(frm);

        frm.refresh_fields();
        frm.__ip_summary_loaded = true;

    } catch (error) {
        console.error("IP Bill Summary loading failed:", error);
        frappe.msgprint(
            "Unable to populate IP Bill Summary. Check the browser console."
        );
    } finally {
        if (isCurrentRequest()) {
            frm.__ip_summary_loading = false;
        }
    }
}

// Keep all totals synchronized for every charge field.
const IP_BILL_CHARGE_FIELDS = [
    "theatre_charges",
    "surgeon_charge",
    "assisting_charges",
    "c_arm_charges",
    "room_charges",
    "consultant_doctor_charges",
    "medicines_consumables",
    "sicu_charges",
    "anaesthesia_charge",
    "implant_charges"
];

frappe.ui.form.on("IP Bill Summary", {
    total_charges(frm) {
        if (frm.doc.docstatus === 0) {
            calculate_final_payable_amount(frm);
        }
    },

    theatre_charges: update_total_charges,
    surgeon_charge: update_total_charges,
    assisting_charges: update_total_charges,
    c_arm_charges: update_total_charges,
    room_charges: update_total_charges,
    consultant_doctor_charges: update_total_charges,
    medicines_consumables: update_total_charges,
    sicu_charges: update_total_charges,
    anaesthesia_charge: update_total_charges,
    implant_charges: update_total_charges,

    amount_paid(frm) {
        calculate_final_payable_amount(frm);
    }
});

async function update_total_charges(frm) {
    if (frm.doc.docstatus !== 0) return;

    const total = IP_BILL_CHARGE_FIELDS.reduce(
        (sum, fieldname) => sum + flt(frm.doc[fieldname]),
        0
    );

    if (flt(frm.doc.total_charges) !== total) {
        await frm.set_value("total_charges", total);
    }

    await calculate_final_payable_amount(frm);
}

window.open_source_invoice_dialog = function(frm) {
    if (!frm.doc.inpatient_record) {
        frappe.msgprint(__("Select an Inpatient Record first."));
        return;
    }

    frappe.call({
        method: "selvi_hospital.ip_bill_import.get_available_source_invoices",
        args: {
            inpatient_record: frm.doc.inpatient_record,
            summary_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __("Loading submitted Sales Invoices..."),
        callback(r) {
            if (r.exc) return;

            const invoices = r.message || [];

            const rows = invoices.map(inv => {
                const unavailable = Boolean(inv.already_imported);
                const disabled = unavailable ? "disabled" : "";

                return `
                    <tr>
                        <td>
                            <input type="checkbox"
                                class="ip-source-invoice-check"
                                value="${frappe.utils.escape_html(inv.name)}"
                                ${disabled}>
                        </td>
                        <td>${frappe.utils.escape_html(inv.name)}</td>
                        <td>${frappe.utils.escape_html(String(inv.posting_date || ""))}</td>
                        <td class="text-right">
                            ${format_currency(inv.grand_total)}
                        </td>
                        <td>
                            ${unavailable
                                ? __("Already imported into {0}", [
                                    frappe.utils.escape_html(inv.imported_in || "")
                                ])
                                : __("Available")}
                        </td>
                    </tr>`;
            }).join("");

            const dialog = new frappe.ui.Dialog({
                title: __("Import Sales Invoices"),
                size: "extra-large",
                fields: [{
                    fieldtype: "HTML",
                    fieldname: "invoice_list"
                }],
                primary_action_label: __("Import Selected"),
                primary_action() {
                    const selected = dialog.$wrapper
                        .find(".ip-source-invoice-check:checked")
                        .map(function () {
                            return this.value;
                        }).get();

                    if (!selected.length) {
                        frappe.msgprint(__("Select at least one invoice."));
                        return;
                    }

                    const existing = new Set(
                        (frm.doc.source_invoices || [])
                            .map(row => row.source_invoice)
                    );

                    const duplicates = selected.filter(name => existing.has(name));

                    if (duplicates.length) {
                        frappe.msgprint(
                            __("These invoices are already in this summary: {0}", [
                                duplicates.join(", ")
                            ])
                        );
                        return;
                    }

                    const import_selected_invoices = () => {
                        frappe.call({
                            method: "selvi_hospital.ip_bill_import.import_source_invoices",
                            args: {
                                summary_name: frm.doc.name,
                                invoice_names: selected
                            },
                            freeze: true,
                            freeze_message: __("Importing invoices..."),
                            callback(result) {
                                if (result.exc) return;

                                const importedCount = result.message?.imported_count;

                                if (importedCount !== selected.length) {
                                    frappe.msgprint(
                                        __("Import was not confirmed. Refresh the form and check the imported invoice rows.")
                                    );
                                    return;
                                }

                                dialog.hide();
                                frm.reload_doc().then(() => {
                                    frappe.show_alert({
                                        message: __("{0} source invoice(s) imported successfully.", [
                                            importedCount
                                        ]),
                                        indicator: "green"
                                    });
                                });
                            }
                        });
                    };

                    if (frm.is_new()) {
                        frm.save()
                            .then(() => {
                                if (!frm.doc.name) {
                                    frappe.msgprint(
                                        __("The IP Bill Summary could not be saved.")
                                    );
                                    return;
                                }
                                import_selected_invoices();
                            })
                            .catch(() => {});
                        return;
                    }

                    import_selected_invoices();
                }
            });

            dialog.fields_dict.invoice_list.$wrapper.html(`
                <div class="mb-3">
                    ${__("Select submitted invoices belonging to this admission.")}
                    ${__("Invoices already imported elsewhere are disabled.")}
                </div>
                <div style="overflow-x:auto">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>${__("Select")}</th>
                                <th>${__("Sales Invoice")}</th>
                                <th>${__("Posting Date")}</th>
                                <th class="text-right">${__("Total Including GST")}</th>
                                <th>${__("Import Status")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows || `<tr><td colspan="5">${__("No submitted invoices found.")}</td></tr>`}
                        </tbody>
                    </table>
                </div>
            `);

            dialog.show();
        }
    });
}
