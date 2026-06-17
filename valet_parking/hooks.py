app_name = "valet_parking"
app_title = "Valet Parking"
app_publisher = "Rajesh"
app_description = "WhatsApp-based Valet Parking Management"
app_email = "rajeshgadapa25@gmail.com"
app_license = "mit"

# Apps
# ------------------

# frappe_whatsapp and frappe_whatsapp_chatbot are both required:
#   frappe_whatsapp  — WhatsApp Message doctype & outbound sending
#   frappe_whatsapp_chatbot — routes inbound messages; calls our keyword scripts
required_apps = ["frappe_whatsapp", "frappe_whatsapp_chatbot"]

# Fixtures — exported to valet_parking/fixtures/ and imported on bench migrate
# NOTE: WhatsApp Keyword Reply uses autoname format:{title}-{#####} so it cannot
# be imported via fixtures. The two valet keyword replies ("Valet PARK" and
# "Valet Get My Car") were seeded directly via bench console.
# See: valet_parking/fixtures/whatsapp_keyword_reply.json for reference.

doc_events = {
    "Parking Ticket": {
        "on_update": "valet_parking.valet_parking.whatsapp.outbound.on_ticket_update",
    },
    # WhatsApp Message inbound is now handled by frappe_whatsapp_chatbot.
    # Valet logic is invoked via chatbot Keyword Reply scripts:
    #   - "PARK" keyword  → valet_parking.valet_parking.whatsapp.inbound.handle_park_keyword
    #   - button reply    → valet_parking.valet_parking.whatsapp.inbound.handle_retrieval_button
}

exempt_from_csrf_checks = [
    "valet_parking.valet_parking.api.api.update_ticket_status",
    "valet_parking.valet_parking.api.api.get_tickets",
    "valet_parking.valet_parking.api.api.get_ticket",
    "valet_parking.valet_parking.api.api.get_dashboard_counts",
    "valet_parking.valet_parking.api.api.get_daily_summary",
    "valet_parking.valet_parking.api.api.get_available_tags",
]
# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "valet_parking",
# 		"logo": "/assets/valet_parking/logo.png",
# 		"title": "Valet Parking",
# 		"route": "/valet_parking",
# 		"has_permission": "valet_parking.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/valet_parking/css/valet_parking.css"
# app_include_js = "/assets/valet_parking/js/valet_parking.js"

# include js, css files in header of web template
# web_include_css = "/assets/valet_parking/css/valet_parking.css"
# web_include_js = "/assets/valet_parking/js/valet_parking.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "valet_parking/public/scss/website"

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
# app_include_icons = "valet_parking/public/icons.svg"

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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "valet_parking.utils.jinja_methods",
# 	"filters": "valet_parking.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "valet_parking.install.before_install"
# after_install = "valet_parking.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "valet_parking.uninstall.before_uninstall"
# after_uninstall = "valet_parking.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "valet_parking.utils.before_app_install"
# after_app_install = "valet_parking.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "valet_parking.utils.before_app_uninstall"
# after_app_uninstall = "valet_parking.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "valet_parking.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
# (Business logic doc_events live in valet_parking/valet_parking/hooks.py)

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"valet_parking.tasks.all"
# 	],
# 	"daily": [
# 		"valet_parking.tasks.daily"
# 	],
# 	"hourly": [
# 		"valet_parking.tasks.hourly"
# 	],
# 	"weekly": [
# 		"valet_parking.tasks.weekly"
# 	],
# 	"monthly": [
# 		"valet_parking.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "valet_parking.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "valet_parking.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "valet_parking.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["valet_parking.utils.before_request"]
# after_request = ["valet_parking.utils.after_request"]

# Job Events
# ----------
# before_job = ["valet_parking.utils.before_job"]
# after_job = ["valet_parking.utils.after_job"]

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
# 	"valet_parking.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []