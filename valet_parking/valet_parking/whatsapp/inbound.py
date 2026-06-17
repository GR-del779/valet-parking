import frappe


# valet_parking/valet_parking/whatsapp/inbound.py
#
# Inbound WhatsApp messages are routed through frappe_whatsapp_chatbot.
# The chatbot's Keyword Reply doctype calls the two public functions below.
#
# IMPORTANT — how the chatbot calls script methods:
#   frappe.call(script, doc=message_doc)
#   Only `doc` is passed as a keyword argument. All other args default to None
#   and are extracted from the doc itself inside each handler.


# ─────────────────────────────────────────────────────────────────────────────
# Public script functions — called by frappe_whatsapp_chatbot Keyword Reply
# ─────────────────────────────────────────────────────────────────────────────

def handle_park_keyword(doc, **kwargs):
    """
    Chatbot script entry point for PARK messages.

    The chatbot calls:  frappe.call(script, doc=message_doc)
    So only `doc` is guaranteed. Phone, message, and account are
    extracted from the doc itself.
    """
    phone = str(doc.get("from") or "")
    msg   = doc.message or ""
    acct  = getattr(doc, "whatsapp_account", None)
    name  = getattr(doc, "profile_name", "") or ""

    parts = msg.strip().upper().split()
    token_hint = parts[1] if len(parts) > 1 else ""

    _create_or_claim_ticket(phone, name, doc.name, token_hint, whatsapp_account=acct)

    # Return True so the chatbot processor treats this as "handled" and skips
    # its default fallback response. send_response(True) is a silent no-op
    # (True is neither str nor dict) but the early `return` prevents the
    # default "Sorry, I didn't understand" message from being sent.
    return True


def handle_retrieval_button(doc, **kwargs):
    """
    Chatbot script entry point for the 'Get My Car' interactive button.

    The chatbot calls:  frappe.call(script, doc=message_doc)
    Only `doc` is guaranteed.
    """
    phone = str(doc.get("from") or "")
    acct  = getattr(doc, "whatsapp_account", None)

    _request_retrieval(phone, whatsapp_account=acct)

    # Return True so the chatbot processor treats this as "handled" and skips
    # its default fallback response (same reasoning as handle_park_keyword).
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Core business logic (private helpers)
# ─────────────────────────────────────────────────────────────────────────────

def _create_or_claim_ticket(phone, name, msg_doc_name, token_hint, whatsapp_account=None):
    """
    Smart ticket handling with Key Tag support:
    1. If token_hint matches a Key Tag (e.g. KT-007):
       a. Tag is Available → create a new ticket linked to this tag
       b. Tag is In Use, ticket has no customer_phone → claim the existing ticket
       c. Tag is In Use, ticket has customer_phone → tell them it's already in use
    2. If token_hint matches an unclaimed ticket (legacy token) → claim it
    3. If phone already has an active ticket → remind them
    4. Otherwise → create a new ticket (no tag, random token)
    """

    # ── Step 1: Check if token_hint matches a Key Tag ──────────────────────
    if token_hint and frappe.db.exists("Key Tag", token_hint):
        tag = frappe.get_doc("Key Tag", token_hint)

        if tag.status == "Available":
            ticket = frappe.get_doc({
                "doctype": "Parking Ticket",
                "key_tag": tag.name,
                "customer_phone": phone,
                "customer_name": name,
                "whatsapp_message_id": msg_doc_name,
            })
            ticket.insert(ignore_permissions=True)
            frappe.db.commit()

            _send_message(phone,
                f"Your valet request has been received!\n\n"
                f"Tag: *{tag.tag_number}*\n"
                f"Status: Awaiting Parking\n\n"
                f"You will get a WhatsApp message once your vehicle is parked.",
                whatsapp_account=whatsapp_account)
            return

        elif tag.status == "In Use" and tag.current_ticket:
            ticket = frappe.get_doc("Parking Ticket", tag.current_ticket)

            if not ticket.customer_phone:
                ticket.customer_phone = phone
                ticket.customer_name = name
                ticket.whatsapp_message_id = msg_doc_name
                ticket.save(ignore_permissions=True)
                frappe.db.commit()

                _send_message(phone,
                    f"Your valet request has been received!\n\n"
                    f"Tag: *{tag.tag_number}*\n"
                    f"Status: {ticket.status}\n\n"
                    f"You will get a WhatsApp message once your vehicle is parked.",
                    whatsapp_account=whatsapp_account)
            else:
                _send_message(phone,
                    f"Tag *{tag.tag_number}* is currently in use. "
                    f"Please check with the valet desk.",
                    whatsapp_account=whatsapp_account)
            return

    # ── Step 2: Legacy — check if token_hint matches an unclaimed ticket ────
    if token_hint:
        unclaimed = frappe.db.get_value(
            "Parking Ticket",
            {
                "token_number": token_hint,
                "customer_phone": ["in", ["", None]],
                "status": ["not in", ["Delivered"]],
            },
            "name"
        )
        if unclaimed:
            ticket = frappe.get_doc("Parking Ticket", unclaimed)
            ticket.customer_phone = phone
            ticket.customer_name = name
            ticket.whatsapp_message_id = msg_doc_name
            ticket.save(ignore_permissions=True)
            frappe.db.commit()

            _send_message(phone,
                f"Your valet request has been received!\n\n"
                f"Token: *{ticket.token_number}*\n"
                f"Status: Awaiting Parking\n\n"
                f"You will get a WhatsApp message once your vehicle is parked.",
                whatsapp_account=whatsapp_account)
            return

    # ── Step 3: Check if this phone already has an active ticket ────────────
    existing = frappe.db.get_value(
        "Parking Ticket",
        {"customer_phone": phone, "status": ["not in", ["Delivered"]]},
        "name"
    )
    if existing:
        ticket = frappe.get_doc("Parking Ticket", existing)
        _send_message(phone,
            f"You already have an active ticket *{ticket.token_number}* "
            f"(Status: {ticket.status}). Please wait for your vehicle.",
            whatsapp_account=whatsapp_account)
        return

    # ── Step 4: Create a brand new ticket (no key tag, random token) ────────
    ticket = frappe.get_doc({
        "doctype": "Parking Ticket",
        "customer_phone": phone,
        "customer_name": name,
        "whatsapp_message_id": msg_doc_name,
    })
    ticket.insert(ignore_permissions=True)
    frappe.db.commit()

    _send_message(phone,
        f"Your valet request has been received!\n\n"
        f"Token: *{ticket.token_number}*\n"
        f"Status: Awaiting Parking\n\n"
        f"You will get a WhatsApp message once your vehicle is parked.",
        whatsapp_account=whatsapp_account)


def _request_retrieval(phone, whatsapp_account=None):
    """Handle 'Get My Car' button — update ticket to Retrieval Requested."""
    ticket_name = frappe.db.get_value(
        "Parking Ticket",
        {"customer_phone": phone, "status": "Parked"},
        "name"
    )
    if not ticket_name:
        _send_message(phone,
            "No parked vehicle found for your number. Please contact the valet desk.",
            whatsapp_account=whatsapp_account)
        return

    ticket = frappe.get_doc("Parking Ticket", ticket_name)
    ticket.status = "Retrieval Requested"
    ticket.save(ignore_permissions=True)
    frappe.db.commit()

    _send_message(phone,
        "Got it! We are fetching your vehicle. "
        "Please make your way to the valet pickup area.",
        whatsapp_account=whatsapp_account)


def _send_message(phone, text, whatsapp_account=None):
    """
    Send a plain text WhatsApp message via frappe_whatsapp.
    Sets ignore_chatbot flag so the chatbot processor does not re-handle
    this outgoing message and cause a loop.
    """
    try:
        payload = {
            "doctype": "WhatsApp Message",
            "type": "Outgoing",
            "to": phone,
            "message_type": "Manual",
            "content_type": "text",
            "message": text,
        }
        if whatsapp_account:
            payload["whatsapp_account"] = whatsapp_account

        msg = frappe.get_doc(payload)
        msg.flags.ignore_chatbot = True   # prevent chatbot processing loop
        msg.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="WhatsApp Send Error", message=str(e))