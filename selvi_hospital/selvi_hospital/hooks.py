app_name = "selvi_hospital"
app_title = "Selvi Hospital Custom App"
app_publisher = "CubaAR"
app_description = "Customizations for Selvi Hospital"
app_email = "cubaar29@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "selvi_hospital",
# 		"logo": "/assets/selvi_hospital/logo.png",
# 		"title": "Selvi Hospital Custom App",
# 		"route": "/selvi_hospital",
# 		"has_permission": "selvi_hospital.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/selvi_hospital/css/selvi_hospital.css"
app_include_js = "/assets/selvi_hospital/js/ip_bill_summary.js"

# include js, css files in header of web template
# web_include_css = "/assets/selvi_hospital/css/selvi_hospital.css"
# web_include_js = "/assets/selvi_hospital/js/selvi_hospital.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "selvi_hospital/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "selvi_hospital/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "selvi_hospital.utils.jinja_methods",
# 	"filters": "selvi_hospital.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "selvi_hospital.install.before_install"
# after_install = "selvi_hospital.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "selvi_hospital.uninstall.before_uninstall"
# after_uninstall = "selvi_hospital.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "selvi_hospital.utils.before_app_install"
# after_app_install = "selvi_hospital.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "selvi_hospital.utils.before_app_uninstall"
# after_app_uninstall = "selvi_hospital.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "selvi_hospital.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "selvi_hospital.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {

# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"selvi_hospital.tasks.all"
# 	],
# 	"daily": [
# 		"selvi_hospital.tasks.daily"
# 	],
# 	"hourly": [
# 		"selvi_hospital.tasks.hourly"
# 	],
# 	"weekly": [
# 		"selvi_hospital.tasks.weekly"
# 	],
# 	"monthly": [
# 		"selvi_hospital.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "selvi_hospital.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "selvi_hospital.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "selvi_hospital.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "selvi_hospital.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["selvi_hospital.utils.before_request"]
# after_request = ["selvi_hospital.utils.after_request"]

# Job Events
# ----------
# before_job = ["selvi_hospital.utils.before_job"]
# after_job = ["selvi_hospital.utils.after_job"]


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"selvi_hospital.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
fixtures = [
    {"dt": "Client Script"},
    {"dt": "Role Profile"},
    {"dt": "Custom DocPerm"},
    {
        "dt": "Notification",
        "filters": [["is_standard", "=", 0]]
    },
    {"dt": "Server Script"},
    {"dt": "Workspace"},
    {
        "dt": "Workspace Sidebar",
        "filters": [
            ["name", "in", [
                "Healthcare",
                "Outpatient",
                "Reception",
                "Inpatient",
                "Users",
                "Lab",
                "Pharmacy",
                "Nurse",
                "Practitioner",
            ]]
        ]
    },
    {
        "dt": "Desktop Icon",
        "filters": [
            ["name", "in", [
                "Healthcare",
                "Outpatient",
                "Reception",
                "Inpatient",
                "Users",
                "Lab",
                "Pharmacy",
            ]]
        ]
    },
    {
        "dt": "Print Format",
        "filters": [
            ["name", "in", [
                "Bill Format 2",
                "Bill Summary  Print",
                "Bill",
                "Bill New",
                "Sales Invoice Bill",
            ]]
        ]
    },
    {"dt": "Property Setter"},
    {"dt": "Custom Field"},
]
# Custom JavaScript for DocTypes
doctype_js = {
    'Sales Invoice': 'public/js/sales_invoice.js',
    'IP Bill Summary': 'public/js/ip_bill_summary.js',
    'Inpatient Record': 'public/js/inpatient_record_ip_bill_summary.js',
    'Clinical Procedure': 'public/js/clinical_procedure.js',
    'Patient Encounter': 'public/js/patient_encounter.js',
    'Purchase Receipt': 'public/js/purchase_receipt.js',
    'Purchase Invoice': 'public/js/purchase_invoice.js',
}

# Custom document events
doc_events = {
    "Patient Appointment": {
        "before_validate": "selvi_hospital.patient_appointment.set_visit_case_type",
    },
    "Purchase Invoice": {
        "validate": "selvi_hospital.purchase_invoice.calculate_purchase_invoice_totals",
    },
    "Patient Encounter": {
        "on_update": "selvi_hospital.follow_up.sync_patient_follow_up",
    },
    'Sales Invoice': {
        'before_validate': 'selvi_hospital.sales_invoice.set_inpatient_practitioner',
        'validate': [
            'selvi_hospital.purchase_receipt.fetch_sales_invoice_batch_mrp_expiry',
        ],
        'before_save': [
            'selvi_hospital.purchase_receipt.apply_op_ip_discount',
            'selvi_hospital.sales_invoice.calculate_advance_balance',
        ],
        'after_insert': 'selvi_hospital.ip_bill_summary.link_consolidated_invoice',
        'on_submit': 'selvi_hospital.ip_bill_summary.sync_from_sales_invoice',
        'on_update_after_submit': 'selvi_hospital.ip_bill_summary.sync_from_sales_invoice',
    },
    'IP Bill Summary': {
        'validate': [
            'selvi_hospital.ip_bill_summary.calculate_total_charges',
            'selvi_hospital.ip_bill_import.validate_source_invoice_import',
        ],
        'before_submit': 'selvi_hospital.ip_bill_summary.validate_before_submit',
        'on_update': 'selvi_hospital.ip_bill_summary.sync_sales_invoice_link',
        'on_update_after_submit': 'selvi_hospital.ip_bill_summary.sync_sales_invoice_link',
    },
    'Payment Entry': {
        'on_submit': 'selvi_hospital.ip_bill_summary.sync_from_payment_entry',
        'on_cancel': 'selvi_hospital.ip_bill_summary.sync_from_payment_entry',
    },
}

# Purchase Receipt: save MRP and expiry in the generated Batch
doc_events.setdefault("Purchase Receipt", {})["validate"] = (
    "selvi_hospital.purchase_receipt.fetch_batch_mrp_expiry"
)

doc_events.setdefault("Purchase Receipt", {})["on_submit"] = (
    "selvi_hospital.purchase_receipt.update_generated_batch_details"
)

# Keep Item Available Batches synchronized with Batch records
doc_events.setdefault("Batch", {}).update({
    "after_insert": "selvi_hospital.purchase_receipt.sync_item_batches_on_update",
    "on_update": "selvi_hospital.purchase_receipt.sync_item_batches_on_update",
})


# Automatic Item Group shelf-life defaults and Batch expiry calculation
doc_events.setdefault("Item", {})["before_validate"] = (
    "selvi_hospital.purchase_receipt.set_item_shelf_life_from_group"
)

doc_events.setdefault("Batch", {})["before_validate"] = (
    "selvi_hospital.purchase_receipt.set_batch_expiry_from_shelf_life"
)


# Automatically populate Item CGST and SGST from the selected tax template.
_item_before_validate = doc_events.setdefault("Item", {}).get("before_validate")

if not _item_before_validate:
    doc_events["Item"]["before_validate"] = [
        "selvi_hospital.purchase_receipt.set_item_gst_from_tax_template"
    ]
elif isinstance(_item_before_validate, str):
    doc_events["Item"]["before_validate"] = [
        _item_before_validate,
        "selvi_hospital.purchase_receipt.set_item_gst_from_tax_template"
    ]
else:
    _item_before_validate.append(
        "selvi_hospital.purchase_receipt.set_item_gst_from_tax_template"
    )



# Automatically set Item Dosage Form from Item Group.
_item_events = doc_events.setdefault("Item", {})
_before_validate = _item_events.get("before_validate")

if not _before_validate:
    _item_events["before_validate"] = [
        "selvi_hospital.purchase_receipt.set_item_dosage_form_from_group"
    ]
elif isinstance(_before_validate, str):
    _item_events["before_validate"] = [
        _before_validate,
        "selvi_hospital.purchase_receipt.set_item_dosage_form_from_group"
    ]
elif "selvi_hospital.purchase_receipt.set_item_dosage_form_from_group" not in _before_validate:
    _before_validate.append(
        "selvi_hospital.purchase_receipt.set_item_dosage_form_from_group"
    )


doctype_js["Medicine Return"] = "public/js/medicine_return.js"

app_include_css = "/assets/selvi_hospital/css/batch_dropdown.css"


override_doctype_class = {
    "Medicine Return": "selvi_hospital.selvi_hospital_custom_app.doctype.medicine_return.medicine_return.MedicineReturn"
}


# Medicine Return Custom DocType event handlers
doc_events.setdefault("Medicine Return", {}).update({
    "validate": "selvi_hospital.selvi_hospital_custom_app.doctype.medicine_return.medicine_return.medicine_return_validate",
    "on_submit": "selvi_hospital.selvi_hospital_custom_app.doctype.medicine_return.medicine_return.medicine_return_on_submit",
    "on_cancel": "selvi_hospital.selvi_hospital_custom_app.doctype.medicine_return.medicine_return.medicine_return_on_cancel",
})
