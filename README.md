# 🚗 WhatsApp-Based Valet Parking Management System

A valet parking management solution built on the **Frappe Framework** that enables customers to interact through **WhatsApp** while valet attendants manage operations using a **Progressive Web Application (PWA)**.

The system eliminates the need for a dedicated customer mobile application by using WhatsApp as the primary communication channel.

---

# Features

* QR code based parking ticket identification
* WhatsApp-based customer interaction
* Automated parking and retrieval notifications
* Parking Ticket lifecycle management
* Progressive Web Application (PWA) for valet attendants
* Real-time ticket status tracking
* REST API integration
* Custom Frappe DocTypes and business workflows

---

# Technology Stack

| Component       | Technology             |
| --------------- | ---------------------- |
| Framework       | Frappe Framework       |
| Backend         | Python                 |
| Database        | MariaDB                |
| Frontend        | HTML, CSS, JavaScript  |
| Messaging       | WhatsApp Cloud API     |
| QR Generation   | Python QR Code Library |
| Version Control | Git & GitHub           |

---

# System Workflow

## Vehicle Drop-Off

1. Customer arrives at the valet parking area.
2. Customer receives a valet token containing a unique QR code.
3. Customer scans the QR code.
4. WhatsApp opens with a pre-filled message.
5. Customer sends the message.
6. A Parking Ticket is automatically created in the system.
7. The valet attendant parks the vehicle.

## Vehicle Retrieval

1. Customer receives a WhatsApp notification after the vehicle is parked.
2. Customer selects the **Get My Car** option.
3. A retrieval request is created.
4. The valet attendant is notified through the PWA dashboard.
5. Vehicle status is updated through the retrieval workflow.
6. Customer receives WhatsApp updates until the vehicle is delivered.

---

# Status Workflow

```text
Awaiting Parking
        ↓
      Parked
        ↓
Retrieval Requested
        ↓
    On The Way
        ↓
    Delivered
```

---

# Project Structure

```text
valet_parking/
│
├── api/
│   └── api.py
│
├── doctype/
│   ├── parking_ticket/
│   └── valet_settings/
│
├── whatsapp/
│   ├── inbound.py
│   └── outbound.py
│
├── qr_code.py
├── hooks.py
│
└── www/
    ├── valet.html
    └── valet.py
```

---

# Core Components

## Parking Ticket DocType

Stores all vehicle parking information including:

* Token Number
* Customer Details
* Vehicle Details
* Parking Status
* Parking Location
* Retrieval Information
* Status Timestamps

## Valet Settings DocType

Stores application configuration such as:

* WhatsApp Phone Number ID
* Access Token
* Webhook Verify Token
* Business Number
* Message Templates

---

# WhatsApp Integration

The system integrates with the WhatsApp Cloud API to:

* Receive customer messages
* Process parking requests
* Send parking confirmations
* Send retrieval notifications
* Handle vehicle delivery updates

---

# Valet Attendant PWA

The Progressive Web Application provides:

* Dashboard view
* Ticket status tracking
* Vehicle retrieval management
* Real-time updates
* Mobile-friendly interface

Accessible through:

```text
https://your-domain.com/valet
```

---

# Installation

## Get the App

```bash
cd ~/frappe-bench

bench get-app https://github.com/GR-del779/valet-parking.git
```

## Install on Site

```bash
bench --site your-site install-app valet_parking
```

## Run Migrations

```bash
bench --site your-site migrate
```

## Restart Bench

```bash
bench restart
```

---

# Development Setup

Start the development server:

```bash
cd ~/frappe-bench

bench start
```

Access Frappe Desk:

```text
http://localhost:8000
```

---

# Future Enhancements

* Live notifications using WebSockets
* Multiple valet locations
* Vehicle image capture
* Analytics dashboard
* QR code batch generation
* SMS fallback notifications

---

# Author

**Rajesh Gadapa**

Computer Science Engineer

GitHub:
https://github.com/GR-del779

Project Repository:
https://github.com/GR-del779/valet-parking

---
