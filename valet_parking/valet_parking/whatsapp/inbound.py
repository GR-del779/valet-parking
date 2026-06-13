import frappe
import json
from frappe import _


@frappe.whitelist(allow_guest=True)
def verify():
    """Meta webhook verification - GET request."""
    settings  = frappe.get_single("Valet Settings")
    mode      = frappe.request.args.get("hub.mode")
    token     = frappe.request.args.get("hub.verify_token")
    challenge = frappe.request.args.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
        frappe.response["type"] = "txt"
        frappe.response["txt"]  = challenge
    else:
        frappe.throw(_("Webhook verification failed"), frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def receive():
    """Meta webhook - handles both GET (verification) and POST (messages)."""

    if frappe.request.method == "GET":
        settings  = frappe.get_single("Valet Settings")
        mode      = frappe.request.args.get("hub.mode")
        token     = frappe.request.args.get("hub.verify_token")
        challenge = frappe.request.args.get("hub.challenge", "")

        if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
            from werkzeug.wrappers import Response
            return Response(challenge, status=200, mimetype="text/plain")
        else:
            from werkzeug.wrappers import Response
            return Response("Forbidden", status=403, mimetype="text/plain")

    try:
        payload = json.loads(frappe.request.data)
    except Exception:
        frappe.response["http_status_code"] = 400
        return {"error": "Invalid JSON"}

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            _process(value)

    frappe.response["http_status_code"] = 200
    return {"status": "ok"}


def _process(value):
    messages = value.get("messages", [])
    contacts = value.get("contacts", [])
    contact_name = contacts[0].get("profile", {}).get("name", "") if contacts else ""

    for msg in messages:
        msg_type    = msg.get("type")
        from_number = "+" + msg.get("from", "")
        msg_id      = msg.get("id", "")

        if msg_type == "text":
            text = msg.get("text", {}).get("body", "").strip().upper()
            if text.startswith("PARK"):
                parts = text.split()
                # Extract token hint if provided e.g. "PARK VP-RDYR"
                token_hint = parts[1] if len(parts) > 1 else ""
                _create_or_claim_ticket(from_number, contact_name, msg_id, token_hint)
            else:
                from valet_parking.valet_parking.whatsapp.outbound import send_plain_text
                send_plain_text(from_number,
                    "Welcome to our Valet Parking! Scan the QR code on your token to get started.")

        elif msg_type == "interactive":
            btn_id = (msg.get("interactive", {})
                         .get("button_reply", {})
                         .get("id", ""))
            if btn_id == "get_my_car":
                _request_retrieval(from_number)


def _create_or_claim_ticket(phone, name, msg_id, token_hint):
    """
    Smart ticket handling:
    1. If token_hint matches an existing unclaimed ticket → claim it
    2. If phone already has an active ticket → remind them
    3. Otherwise → create a new ticket
    """
    from valet_parking.valet_parking.whatsapp.outbound import send_plain_text

    # Step 1: Check if token_hint matches a pre-created unclaimed ticket
    # A ticket is "unclaimed" if it has no customer_phone assigned yet
    if token_hint:
        unclaimed = frappe.db.get_value(
            "Parking Ticket",
            {
                "token_number": token_hint,
                "customer_phone": ["in", ["", None]],
                "status": ["not in", ["Delivered"]]
            },
            "name"
        )
        if unclaimed:
            # Claim this ticket — assign customer's phone to it
            ticket = frappe.get_doc("Parking Ticket", unclaimed)
            ticket.customer_phone = phone
            ticket.customer_name  = name
            ticket.whatsapp_message_id = msg_id
            ticket.save(ignore_permissions=True)
            frappe.db.commit()

            send_plain_text(phone,
                f"Your valet request has been received!\n\n"
                f"Token: *{ticket.token_number}*\n"
                f"Status: Awaiting Parking\n\n"
                f"You will get a WhatsApp message once your vehicle is parked.")
            return

    # Step 2: Check if this phone already has an active ticket
    existing = frappe.db.get_value(
        "Parking Ticket",
        {"customer_phone": phone, "status": ["not in", ["Delivered"]]},
        "name"
    )
    if existing:
        ticket = frappe.get_doc("Parking Ticket", existing)
        send_plain_text(phone,
            f"You already have an active ticket *{ticket.token_number}* "
            f"(Status: {ticket.status}). Please wait for your vehicle.")
        return

    # Step 3: Create a brand new ticket
    ticket = frappe.get_doc({
        "doctype": "Parking Ticket",
        "customer_phone": phone,
        "customer_name": name,
        "whatsapp_message_id": msg_id,
    })
    ticket.insert(ignore_permissions=True)
    frappe.db.commit()

    send_plain_text(phone,
        f"Your valet request has been received!\n\n"
        f"Token: *{ticket.token_number}*\n"
        f"Status: Awaiting Parking\n\n"
        f"You will get a WhatsApp message once your vehicle is parked.")


def _request_retrieval(phone):
    """Handle Get My Car button — update ticket to Retrieval Requested."""
    from valet_parking.valet_parking.whatsapp.outbound import send_plain_text

    ticket_name = frappe.db.get_value(
        "Parking Ticket",
        {"customer_phone": phone, "status": "Parked"},
        "name"
    )
    if not ticket_name:
        send_plain_text(phone,
            "No parked vehicle found for your number. Please contact the valet desk.")
        return

    ticket = frappe.get_doc("Parking Ticket", ticket_name)
    ticket.status = "Retrieval Requested"
    ticket.save(ignore_permissions=True)
    frappe.db.commit()

    send_plain_text(phone,
        "Got it! We are fetching your vehicle. "
        "Please make your way to the valet pickup area.")
