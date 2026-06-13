import frappe
import requests
from frappe.utils import now_datetime


def on_ticket_update(doc, method):
    """
    Called by hooks.py every time a Parking Ticket is saved.
    doc    = the ParkingTicket document instance
    method = the event name ("on_update", etc.)
    """
    frappe.log_error(
        title="WHATSAPP DEBUG 1",
        message=f"Ticket={doc.name}\nStatus={doc.status}"
    )

    if not doc.has_value_changed("status"):
        return
    if not doc.has_value_changed("status"):
        return  # Status did not change, nothing to do

    status = doc.status

    if status == "Parked":
        _send(doc, "parked")

    elif status == "On The Way":
        _send(doc, "on_the_way")

    elif status == "Delivered":
        _send(doc, "delivered")


def _send(doc, event):
    
    """Build message and dispatch — real or test mode."""
    settings = frappe.get_single("Valet Settings")
    phone    = doc.customer_phone
    
    frappe.log_error(
        title="WHATSAPP DEBUG 2",
        message=f"Event={event}\nPhone={phone}"
    )

    # Build message text from template
    template_map = {
        "parked":    settings.msg_parked or "",
        "on_the_way": settings.msg_on_the_way or "",
        "delivered": settings.msg_delivered or "",
    }
    body = (template_map[event]
            .replace("{token}", doc.token_number or "")
            .replace("{venue}", settings.valet_location_name or "Our Venue")
            .replace("{vehicle}", doc.vehicle_number or "your vehicle"))

    # Decide: real send or test mode
    token = settings.get_password("whatsapp_access_token")
    if token and settings.whatsapp_phone_number_id:
        _send_real(phone, body, event, doc, settings)
    else:
        _send_test(phone, body, event, doc)
    
    # Record timestamp of last message sent
    frappe.db.set_value("Parking Ticket", doc.name,
                        "last_whatsapp_sent" if hasattr(doc, "last_whatsapp_sent") else "modified",
                        now_datetime())


def _send_real(phone, body, event, doc, settings):
    """Send actual WhatsApp message via Meta Cloud API."""
    token    = settings.get_password("whatsapp_access_token")
    phone_id = settings.whatsapp_phone_number_id
    url      = f"https://graph.facebook.com/v19.0/{phone_id}/messages"

    # For "parked" event — send interactive button message
    if event == "parked":
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _normalise(phone),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "get_my_car",
                                "title": "Get My Car"
                            }
                        }
                    ]
                }
            }
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _normalise(phone),
            "type": "text",
            "text": {"body": body, "preview_url": False}
        }
    frappe.log_error(
        title="WHATSAPP DEBUG 3",
        message=f"Sending WhatsApp\nPhone={phone}\nEvent={event}"
    )
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            timeout=10
        )
        resp.raise_for_status()
        frappe.logger().info(f"WhatsApp sent to {phone} for event={event}")
    except Exception as e:
        frappe.log_error(title="WhatsApp Send Error",
                         message=f"Phone: {phone}\nEvent: {event}\nError: {e}")
    
    frappe.log_error(
        title="WHATSAPP API RESPONSE",
        message=resp.text
    )


def _send_test(phone, body, event, doc):
    """
    TEST MODE — no real WhatsApp credentials configured.
    Logs the message to Frappe Error Log so you can see exactly
    what would be sent. Check: Desk → Error Log → filter by "WhatsApp TEST"
    """
    frappe.log_error(
        title=f"WhatsApp TEST | {event.upper()} | {doc.token_number}",
        message=(
            f"TO      : {phone}\n"
            f"EVENT   : {event}\n"
            f"TICKET  : {doc.name}\n"
            f"TOKEN   : {doc.token_number}\n"
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
    """Strip + and spaces — WhatsApp API needs digits only."""
    return phone.lstrip("+").replace(" ", "").replace("-", "")


def send_plain_text(phone, body):
    """Utility — send a plain text message directly (used by inbound.py)."""
    settings = frappe.get_single("Valet Settings")
    if settings.whatsapp_access_token and settings.whatsapp_phone_number_id:
        _send_real(phone, body, "plain", None, settings)
    else:
        frappe.log_error(
            title=f"WhatsApp TEST | PLAIN | {phone}",
            message=f"TO: {phone}\n\n{body}"
        )
