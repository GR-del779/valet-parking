# Document event hooks
doc_events = {
    "Parking Ticket": {
        "on_update": "valet_parking.valet_parking.whatsapp.outbound.on_ticket_update",
    }
}

# Skip CSRF validation for valet PWA API endpoints
exempt_from_csrf_checks = [
    "valet_parking.valet_parking.api.api.update_ticket_status",
    "valet_parking.valet_parking.api.api.get_tickets",
    "valet_parking.valet_parking.api.api.get_ticket",
    "valet_parking.valet_parking.api.api.get_dashboard_counts",
    "valet_parking.valet_parking.api.api.get_daily_summary",
]
