import frappe
import qrcode
import io
import base64
from urllib.parse import quote


@frappe.whitelist()
def get_qr_for_ticket(ticket_name):
    """
    Generate a WhatsApp QR code for a parking ticket.
    Returns base64 PNG image + the deeplink URL.
    """
    ticket = frappe.get_doc("Parking Ticket", ticket_name)
    settings = frappe.get_single("Valet Settings")

    # Build the WhatsApp deeplink
    wa_number = (settings.whatsapp_number or "").lstrip("+").replace(" ", "")
    message = f"PARK {ticket.token_number}"
    encoded_msg = quote(message)

    if wa_number:
        deeplink = f"https://wa.me/{wa_number}?text={encoded_msg}"
    else:
        # Fallback if no number configured — just encode the token
        deeplink = f"https://wa.me/?text={encoded_msg}"

    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(deeplink)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "token": ticket.token_number,
        "deeplink": deeplink,
        "qr_base64": img_base64,
        "message": message,
    }


@frappe.whitelist()
def get_qr_for_token(token):
    """
    Generate QR for a raw token string (for pre-printing blank tokens).
    """
    settings = frappe.get_single("Valet Settings")
    wa_number = (settings.whatsapp_number or "").lstrip("+").replace(" ", "")
    message = f"PARK {token}"
    encoded_msg = quote(message)
    deeplink = f"https://wa.me/{wa_number}?text={encoded_msg}" if wa_number else f"https://wa.me/?text={encoded_msg}"

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(deeplink)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    return {
        "token": token,
        "deeplink": deeplink,
        "qr_base64": base64.b64encode(buffer.getvalue()).decode("utf-8"),
    }
