import json

import frappe
from frappe.utils import now_datetime

# valet_parking/valet_parking/whatsapp/outbound.py
#
# frappe_whatsapp migration:
#   - REMOVED: _send_real() direct requests.post() to graph.facebook.com
#   - REMOVED: import requests (no longer needed)
#   - REMOVED: duplicate on_ticket_update() definition
#   - ADDED:   _send_via_app() — creates WhatsApp Message doc via frappe_whatsapp
#   - KEPT:    on_ticket_update() hook (registered in hooks.py)
#   - KEPT:    _send_test() for when use_frappe_whatsapp toggle is off / no credentials
#   - KEPT:    send_plain_text() utility (now routes through frappe_whatsapp)
#   - KEPT:    Key Tag release on Delivered
#   - KEPT:    _normalise() phone formatter


def on_ticket_update(doc, method):
    """
    Called by hooks.py every time a Parking Ticket is saved.
    Sends WhatsApp notification when status changes.
    """
    if not doc.has_value_changed("status"):
        return

    if not doc.customer_phone:
        return

    settings = frappe.get_single("Valet Settings")

    status = doc.status

    if status == "Parked":
        _send(doc, "parked", settings)

    elif status == "On The Way":
        _send(doc, "on_the_way", settings)

    elif status == "Delivered":
        _send(doc, "delivered", settings)


def _send(doc, event, settings):
    """Build message body from template and dispatch via frappe_whatsapp or test mode."""
    phone = doc.customer_phone

    template_map = {
        "parked":     settings.msg_parked or "",
        "on_the_way": settings.msg_on_the_way or "",
        "delivered":  settings.msg_delivered or "",
    }
    body = (template_map[event]
            .replace("{token}", doc.token_number or "")
            .replace("{venue}", settings.valet_location_name or "Our Venue")
            .replace("{vehicle}", doc.vehicle_number or "your vehicle"))

    if settings.get("use_frappe_whatsapp"):
        interactive = event == "parked"
        _send_via_app(phone, body, interactive=interactive)
    else:
        # Test / fallback mode — log to Error Log
        _send_test(phone, body, event, doc)

    if frappe.get_meta("Parking Ticket").has_field("last_whatsapp_sent"):
        frappe.db.set_value(
            "Parking Ticket", doc.name, "last_whatsapp_sent", now_datetime()
        )


def _send_via_app(phone, body, interactive=False):
    try:
        payload = {
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": _normalise(phone),
            "message_type": "Manual",
            "content_type": "interactive" if interactive else "text",
            "message": body,
            "whatsapp_account": "Valet parking",
        }
        if interactive:
            payload["buttons"] = json.dumps([
                {"id": "get_my_car", "title": "Get My Car"},
            ])

        msg = frappe.get_doc(payload)
        msg.insert(ignore_permissions=True)
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(
            title="WhatsApp Send Error",
            message=f"Phone: {phone}\nInteractive: {interactive}\nError: {e}"
        )

def _send_test(phone, body, event, doc):
    """
    TEST MODE — use_frappe_whatsapp toggle is off.
    Logs the message to Frappe Error Log so you can see exactly
    what would be sent. Check: Desk → Error Log → filter by 'WhatsApp TEST'.
    """
    frappe.log_error(
        title=f"WhatsApp TEST | {event.upper()} | {doc.token_number}",
        message=(
            f"TO      : {phone}\n"
            f"EVENT   : {event}\n"
            f"TICKET  : {doc.name}\n"
            f"TOKEN   : {doc.token_number}\n"
            f"KEY TAG : {doc.key_tag or '—'}\n"
            f"─────────────────────────\n"
            f"MESSAGE :\n{body}"
        )
    )
    frappe.msgprint(
        f"📱 <b>WhatsApp TEST MODE</b><br>"
        f"Would send <b>{event}</b> message to <b>{phone}</b><br>"
        f"<small>Check Error Log for full message preview</small>",
        indicator="blue",
        alert=True
    )


def _normalise(phone):
    """Ensure phone is in international format for WhatsApp (digits only, no +)."""
    phone = str(phone).strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        phone = phone[1:]
    elif phone.startswith("0"):
        phone = "91" + phone[1:]
    return phone


def send_plain_text(phone, body):
    """
    Utility called by inbound.py for simple text replies.
    Now routes through frappe_whatsapp instead of direct API call.
    Falls back to test log if use_frappe_whatsapp toggle is off.
    """
    settings = frappe.get_single("Valet Settings")

    if settings.get("use_frappe_whatsapp"):
        _send_via_app(phone, body, interactive=False)
    else:
        frappe.log_error(
            title=f"WhatsApp TEST | PLAIN | {phone}",
            message=f"TO: {phone}\n\n{body}"
        )