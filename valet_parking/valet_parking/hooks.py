# valet_parking/valet_parking/hooks.py
#
# Inner hooks — app-level business logic events.
# frappe_whatsapp migration:
#   - ADDED: WhatsApp Message after_insert → routes inbound messages to our logic
#   - KEPT:  Parking Ticket on_update → sends outbound WhatsApp notifications
#   - KEPT:  exempt_from_csrf_checks for PWA API endpoints

# Skip CSRF validation for valet PWA API endpoints
exempt_from_csrf_checks = [
    "valet_parking.valet_parking.api.api.update_ticket_status",
    "valet_parking.valet_parking.api.api.get_tickets",
    "valet_parking.valet_parking.api.api.get_ticket",
    "valet_parking.valet_parking.api.api.get_dashboard_counts",
    "valet_parking.valet_parking.api.api.get_daily_summary",
    "valet_parking.valet_parking.api.api.get_available_tags",
]

doc_events = {
    "Parking Ticket": {
        "on_update": "valet_parking.valet_parking.whatsapp.outbound.on_ticket_update",
    },
    "WhatsApp Message": {
        "after_insert": "valet_parking.valet_parking.whatsapp.inbound.on_whatsapp_message",
    },
}