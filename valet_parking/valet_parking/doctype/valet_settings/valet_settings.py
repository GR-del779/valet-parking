import frappe
from frappe.model.document import Document

class ValetSettings(Document):
    pass

def get_settings():
    return frappe.get_single("Valet Settings")
