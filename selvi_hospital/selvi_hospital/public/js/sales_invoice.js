async function update_advance_balance(frm) {
    let allocatedAdvance = 0;
    let fullAdvance = 0;
    const paymentEntries = new Set();

    for (const row of (frm.doc.advances || [])) {
        if (
            row.reference_type &&
            row.reference_name &&
            flt(row.allocated_amount) > 0
        ) {
            allocatedAdvance += flt(row.allocated_amount);

            if (row.reference_type === "Payment Entry") {
                paymentEntries.add(row.reference_name);
            }
        }
    }

    for (const paymentEntry of paymentEntries) {
        const result = await frappe.db.get_value(
            "Payment Entry",
            paymentEntry,
            "paid_amount"
        );
        fullAdvance += flt(result.message?.paid_amount);
    }

    const patientPayable = flt(frm.doc.patient_payable_amount);
    const advanceBalance = Math.max(fullAdvance - allocatedAdvance, 0);
    const patientBalance = Math.max(patientPayable - allocatedAdvance, 0);

    if (flt(frm.doc.custom_advance_amount) !== fullAdvance) {
        await frm.set_value("custom_advance_amount", fullAdvance);
    }

    if (flt(frm.doc.custom_advance_balance_amount) !== advanceBalance) {
        await frm.set_value("custom_advance_balance_amount", advanceBalance);
    }

    if (flt(frm.doc.custom_balance_amount) !== patientBalance) {
        await frm.set_value("custom_balance_amount", patientBalance);
    }
}
frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        update_advance_balance(frm);
    },
    patient_payable_amount(frm) {
        update_advance_balance(frm);
    },
    advances_add(frm) {
        update_advance_balance(frm);
    },
    advances_remove(frm) {
        update_advance_balance(frm);
    },
    validate(frm) {
        update_advance_balance(frm);
    }
});

frappe.ui.form.on("Sales Invoice Advance", {
    allocated_amount(frm) {
        update_advance_balance(frm);
    },
    reference_name(frm) {
        update_advance_balance(frm);
    },
    reference_type(frm) {
        update_advance_balance(frm);
    }
});

async function sync_inpatient_practitioner(frm) {
    const inpatient = frm.doc.custom_inpatient_record;
    if (!inpatient) return;

    const result = await frappe.db.get_value(
        "Inpatient Record",
        inpatient,
        "primary_practitioner"
    );

    const practitioner = result.message?.primary_practitioner;
    if (!practitioner) return;

    await frm.set_value("ref_practitioner", practitioner);

    const practitioner_result = await frappe.db.get_value(
        "Healthcare Practitioner",
        practitioner,
        "practitioner_name"
    );

    const practitioner_name =
        practitioner_result.message?.practitioner_name;

    if (practitioner_name) {
        await frm.set_value("custom_doctor_name_", practitioner_name);
    }
}

frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        sync_inpatient_practitioner(frm);
    },
    custom_inpatient_record(frm) {
        sync_inpatient_practitioner(frm);
    }
});
