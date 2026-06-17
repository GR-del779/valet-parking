import frappe
import qrcode
import io
import base64
from urllib.parse import quote


# ── Helpers ──────────────────────────────────────────────────────

def _build_deeplink(token):
    """Build a WhatsApp deeplink URL for the given token string."""
    settings = frappe.get_single("Valet Settings")
    wa_number = (settings.whatsapp_number or "").lstrip("+").replace(" ", "")
    message = f"PARK {token}"
    encoded_msg = quote(message)
    if wa_number:
        return f"https://wa.me/{wa_number}?text={encoded_msg}"
    return f"https://wa.me/?text={encoded_msg}"


def _generate_qr_image(data_url):
    """Generate a QR code PNG as bytes for the given URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# ── Existing APIs (backward-compatible) ──────────────────────────

@frappe.whitelist()
def get_qr_for_ticket(ticket_name):
    """
    Generate a WhatsApp QR code for a parking ticket.
    Returns base64 PNG image + the deeplink URL.
    """
    ticket = frappe.get_doc("Parking Ticket", ticket_name)
    deeplink = _build_deeplink(ticket.token_number)
    img_bytes = _generate_qr_image(deeplink)

    return {
        "token": ticket.token_number,
        "deeplink": deeplink,
        "qr_base64": base64.b64encode(img_bytes).decode("utf-8"),
        "message": f"PARK {ticket.token_number}",
    }


@frappe.whitelist()
def get_qr_for_token(token):
    """
    Generate QR for a raw token string (for pre-printing blank tokens).
    """
    deeplink = _build_deeplink(token)
    img_bytes = _generate_qr_image(deeplink)

    return {
        "token": token,
        "deeplink": deeplink,
        "qr_base64": base64.b64encode(img_bytes).decode("utf-8"),
    }


# ── Key Tag Bulk Operations ──────────────────────────────────────

@frappe.whitelist()
def bulk_create_key_tags(count=50, prefix="KT"):
    """
    Create Key Tag records: KT-001 through KT-050 (or custom count/prefix).
    Skips tags that already exist.
    """
    count = int(count)
    created = []
    skipped = []

    for i in range(1, count + 1):
        tag_number = f"{prefix}-{i:03d}"
        if frappe.db.exists("Key Tag", tag_number):
            skipped.append(tag_number)
            continue

        doc = frappe.get_doc({
            "doctype": "Key Tag",
            "tag_number": tag_number,
            "status": "Available",
        })
        doc.insert(ignore_permissions=True)
        created.append(tag_number)

    frappe.db.commit()
    return {
        "created": created,
        "skipped": skipped,
        "total_created": len(created),
        "total_skipped": len(skipped),
    }


@frappe.whitelist()
def generate_all_key_tag_qrs():
    """
    Generate QR codes for all Key Tags and attach them as files.
    Updates the qr_image and qr_deeplink fields on each Key Tag.
    Skips tags that already have a QR image attached.
    """
    tags = frappe.get_all("Key Tag", fields=["name", "tag_number", "qr_image"])
    generated = []
    skipped = []

    for tag in tags:
        if tag.qr_image:
            skipped.append(tag.tag_number)
            continue

        deeplink = _build_deeplink(tag.tag_number)
        img_bytes = _generate_qr_image(deeplink)

        # Save as a Frappe File attachment
        filename = f"qr_{tag.tag_number}.png"
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "content": base64.b64encode(img_bytes).decode("utf-8"),
            "decode": True,
            "attached_to_doctype": "Key Tag",
            "attached_to_name": tag.name,
            "is_private": 0,
        })
        file_doc.insert(ignore_permissions=True)

        # Update the Key Tag with the file URL and deeplink
        frappe.db.set_value("Key Tag", tag.name, {
            "qr_image": file_doc.file_url,
            "qr_deeplink": deeplink,
        })

        generated.append(tag.tag_number)

    frappe.db.commit()
    return {
        "generated": generated,
        "skipped": skipped,
        "total_generated": len(generated),
        "total_skipped": len(skipped),
    }
