import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
import random
import string


class ParkingTicket(Document):

	def before_insert(self):
		"""Runs before a new ticket is saved to DB for the first time."""
		# If a Key Tag is linked, use its tag_number as the token
		if self.key_tag:
			tag = frappe.get_doc("Key Tag", self.key_tag)
			self.token_number = tag.tag_number
			tag.mark_in_use(self.name or "")
		else:
			# Fallback: generate a random token (no physical tag)
			self.token_number = self._generate_token()

		self.drop_off_time = now_datetime()
		self.status = "Awaiting Parking"

	def after_insert(self):
		"""After the ticket has a name, update the Key Tag's current_ticket reference."""
		if self.key_tag:
			frappe.db.set_value("Key Tag", self.key_tag, "current_ticket", self.name)

	def before_save(self):
		"""Runs every time the document is saved."""
		if self.has_value_changed("status"):
			self._set_status_timestamp()

			# When delivered, release the Key Tag back to Available
			if self.status == "Delivered" and self.key_tag:
				tag = frappe.get_doc("Key Tag", self.key_tag)
				tag.release()

	def _generate_token(self):
		"""Generate a short token like VP-A3K7."""
		chars = string.ascii_uppercase + string.digits
		suffix = "".join(random.choices(chars, k=4))
		return f"VP-{suffix}"

	def _set_status_timestamp(self):
		"""Record the exact time each status was reached."""
		ts = now_datetime()
		mapping = {
			"Parked": "parked_time",
			"Retrieval Requested": "retrieval_requested_time",
			"On The Way": "on_the_way_time",
			"Delivered": "delivered_time",
		}
		field = mapping.get(self.status)
		if field:
			self.set(field, ts)
