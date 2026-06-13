import frappe
from frappe.utils import now_datetime, get_datetime


@frappe.whitelist()
def get_dashboard_counts():
    """Return ticket counts per status for the PWA dashboard."""
    statuses = ["Awaiting Parking", "Parked", "Retrieval Requested", "On The Way"]
    counts = {}
    for s in statuses:
        counts[s] = frappe.db.count("Parking Ticket", {"status": s})
    return counts


@frappe.whitelist()
def get_tickets(status=None, search=None, limit=50):
    """
    Return list of tickets.
    status  = filter by status (optional)
    search  = search token, phone, vehicle number (optional)
    limit   = max records to return
    """
    filters = {}
    if status:
        filters["status"] = status
    else:
        # Default: all active (not delivered)
        filters["status"] = ["not in", ["Delivered"]]

    fields = [
        "name", "token_number", "status",
        "customer_phone", "customer_name",
        "vehicle_number", "vehicle_make", "vehicle_color",
        "parking_location", "drop_off_time", "parked_time",
        "retrieval_requested_time", "assigned_attendant"
    ]

    if search:
        search = search.strip().upper()
        tickets = frappe.db.get_all(
            "Parking Ticket",
            filters=filters,
            or_filters={
                "token_number": ["like", f"%{search}%"],
                "customer_phone": ["like", f"%{search}%"],
                "vehicle_number": ["like", f"%{search}%"],
            },
            fields=fields,
            limit=int(limit),
            order_by="creation desc"
        )
    else:
        tickets = frappe.db.get_all(
            "Parking Ticket",
            filters=filters,
            fields=fields,
            limit=int(limit),
            order_by="creation desc"
        )

    return tickets


@frappe.whitelist()
def get_ticket(ticket_name):
    """Return full details of a single ticket."""
    doc = frappe.get_doc("Parking Ticket", ticket_name)
    return doc.as_dict()


@frappe.whitelist(methods=["POST"])
def update_ticket_status(ticket_name, new_status,
                          parking_location=None, vehicle_number=None,
                          vehicle_make=None, vehicle_color=None, notes=None):
    """
    Update ticket status from the PWA.
    Validates that the transition is allowed before saving.
    """
    allowed_transitions = {
        "Awaiting Parking": "Parked",
        "Parked":           "Retrieval Requested",
        "Retrieval Requested": "On The Way",
        "On The Way":       "Delivered",
    }

    ticket = frappe.get_doc("Parking Ticket", ticket_name)

    # Validate transition
    expected = allowed_transitions.get(ticket.status)
    if new_status != expected:
        frappe.throw(f"Cannot change status from '{ticket.status}' to '{new_status}'")

    # Update fields
    ticket.status = new_status
    if parking_location: ticket.parking_location = parking_location
    if vehicle_number:   ticket.vehicle_number   = vehicle_number
    if vehicle_make:     ticket.vehicle_make      = vehicle_make
    if vehicle_color:    ticket.vehicle_color     = vehicle_color
    if notes:            ticket.notes             = notes

    # Auto-assign attendant
    if not ticket.assigned_attendant:
        ticket.assigned_attendant = frappe.session.user

    ticket.save(ignore_permissions=True)
    frappe.db.commit()

    # Explicitly trigger WhatsApp notification
    from valet_parking.valet_parking.whatsapp.outbound import _send
    _send(ticket, new_status.lower().replace(" ", "_"))

    return {"success": True, "status": ticket.status}


@frappe.whitelist()
def get_daily_summary(date=None):
    """Return stats for a given date (default today)."""
    from frappe.utils import today
    target = date or today()

    total = frappe.db.count("Parking Ticket", {
        "drop_off_time": ["between",
            [f"{target} 00:00:00", f"{target} 23:59:59"]]
    })
    delivered = frappe.db.count("Parking Ticket", {
        "drop_off_time": ["between",
            [f"{target} 00:00:00", f"{target} 23:59:59"]],
        "status": "Delivered"
    })

    # Calculate average turnaround time
    delivered_tickets = frappe.db.get_all(
        "Parking Ticket",
        filters={
            "status": "Delivered",
            "delivered_time": ["between",
                [f"{target} 00:00:00", f"{target} 23:59:59"]]
        },
        fields=["drop_off_time", "delivered_time"]
    )

    avg_minutes = 0
    if delivered_tickets:
        total_mins = sum(
            (get_datetime(t.delivered_time) - get_datetime(t.drop_off_time))
            .total_seconds() / 60
            for t in delivered_tickets
            if t.drop_off_time and t.delivered_time
        )
        avg_minutes = round(total_mins / len(delivered_tickets), 1)

    return {
        "date": target,
        "total": total,
        "delivered": delivered,
        "active": total - delivered,
        "avg_turnaround_minutes": avg_minutes
    }
