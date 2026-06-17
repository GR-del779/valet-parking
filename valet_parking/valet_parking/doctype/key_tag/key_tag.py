import frappe
from frappe.model.document import Document


class KeyTag(Document):

	def validate(self):
		"""Prevent marking a tag In Use if it's already In Use."""
		if self.has_value_changed("status") and self.status == "In Use":
			if self.get_db_value("status") == "In Use":
				frappe.throw(f"Key Tag {self.tag_number} is already in use.")

	def mark_in_use(self, ticket_name):
		"""Assign this key tag to a parking ticket."""
		if self.status == "In Use":
			frappe.throw(
				f"Key Tag {self.tag_number} is already in use"
				f" (Ticket: {self.current_ticket})."
			)
		self.status = "In Use"
		self.current_ticket = ticket_name
		self.save(ignore_permissions=True)

	def release(self):
		"""Release this key tag back to the available pool."""
		self.status = "Available"
		self.current_ticket = None
		self.save(ignore_permissions=True)
