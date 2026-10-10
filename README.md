# BookEase — Professional Universal Booking Agent

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-0F172A?logo=windowsterminal&logoColor=white)](https://customtkinter.tomschimansky.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20SQLAlchemy%20%7C%20Alembic-003B57?logo=sqlite&logoColor=white)](https://www.sqlalchemy.org/)
[![Reports](https://img.shields.io/badge/Reports-ReportLab%20%7C%20openpyxl%20%7C%20Matplotlib-E11D48)](https://www.reportlab.com/)
[![Tests](https://img.shields.io/badge/Tests-15%2F15%20Passing%20(pytest)-10B981?logo=pytest&logoColor=white)](https://docs.pytest.org/)

**BookEase** is a desktop booking and practice management system built with Python and CustomTkinter for clinics, medical aesthetics, salons, consulting practices, and professional service studios.

It runs locally with SQLite, SQLAlchemy ORM, and Alembic database migrations. It relies on deterministic Python availability logic and concurrency-safe database transactions.

---

## 1. Key Features & Capabilities

- **✨ Modern Executive Dashboard**:
  - Live statistics: Today's scheduled visits, projected daily revenue, total clients, completion rates.
  - Interactive 7-day revenue trend bar chart embedded via Matplotlib.
  - Live feed of today's appointments with instant "Complete" and "Cancel" actions.
- **🧙 Guided Booking Assistant (4-Step Wizard)**:
  - Step 1: Browse active treatment services and categories with duration and pricing.
  - Step 2: Choose assigned and qualified specialists with role titles.
  - Step 3: Pick target date and dynamic time slot grid calculated in real-time by the availability engine.
  - Step 4: Search existing clients or register new customer details and confirm booking.
- **🛡 Concurrency-Safe Double-Booking Prevention**:
  - Validates staff working hours, lunch breaks, and approved vacations/leaves.
  - Enforces database transaction locks to prevent overlapping appointments.
- **📅 Interactive Multi-Perspective Calendar**:
  - **Day View**: Chronological hourly schedule feed.
  - **Week View**: 7-day columns with color-coded appointment cards.
  - **Month View**: Calendar grid with appointment counts and quick-jump day views.
  - Filter by specialist or view all staff simultaneously.
- **👥 Client Profiles & History**:
  - Full client directory with search by name, phone, or email.
  - Lifetime appointment histories, spending metrics, and clinical notes.
- **🩺 Specialist & Working Hours Management**:
  - Configure weekly schedules per staff member (custom start/end times and lunch breaks).
  - Vacation and leave tracker that blocks out booking time slots.
  - Service authorization checkboxes.
- **🏷 Service Catalog & Pricing**:
  - Category organization, appointment durations, turnaround buffer times, and pricing.
- **📈 Reports & Analytics**:
  - Custom date range and preset filters (Today, 7 Days, 30 Days).
  - One-click PDF generation via ReportLab.
  - Formatted Excel workbooks via openpyxl.
  - Raw CSV dataset exports.
- **💾 Backups, Integrity, & Audit Trail**:
  - Manual and snapshot database backups with SHA256 integrity verification.
  - SQLite database integrity diagnostic tool (`PRAGMA integrity_check`).
  - Immutable audit logs recording all administrative, booking, and security events.
- **🔐 Security & Role-Based Access Control**:
  - Password hashing with bcrypt.
  - Granular permissions for Administrator, Owner, and Staff roles.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.13 (64-bit) |
| **GUI Framework** | CustomTkinter, Pillow, tkcalendar, babel |
| **Database & ORM** | SQLite, SQLAlchemy 2.0, Alembic migrations |
| **Analytics & Data** | Pandas, NumPy |
| **Reports & Visuals** | Matplotlib, ReportLab, openpyxl |
| **Security & Auth** | bcrypt, Pydantic |
| **Testing** | pytest, pytest-cov |
| **Packaging** | PyInstaller for Windows |

---

## 3. Architecture & Directory Layout

```
Booking_Agent_Project/
├── alembic/                    # Alembic migration environment
│   ├── versions/               # Versioned migration scripts
│   └── env.py
├── alembic.ini                 # Alembic configuration
├── assets/                     # Application icons and theme assets
├── backups/                    # Point-in-time SQLite backups and JSON metadata
├── data/                       # Local SQLite database (bookease.db)
├── reports_output/             # Exported PDF, Excel, and CSV files
├── src/
│   ├── config.py               # Paths, constants, business defaults, roles
│   ├── database/
│   │   ├── connection.py       # Engine, scoped session, WAL mode, init_db
│   │   ├── models.py           # SQLAlchemy ORM declarative models
│   │   └── seed_data.py        # Default admin account, business profile, demo records
│   ├── core/
│   │   ├── security.py         # Bcrypt password hashing, session manager, RBAC
│   │   ├── availability.py     # Slot computation engine, break & leave filters
│   │   ├── booking_service.py  # Concurrency-safe booking, rescheduling, cancellations
│   │   ├── reports_service.py  # ReportLab PDF, openpyxl Excel, and CSV exports
│   │   ├── notifications.py    # Optional SMTP email confirmations & local preview logs
│   │   ├── backup_manager.py   # Database backup, restore, and SHA256 hash checks
│   │   └── audit_logger.py     # Immutable action trail logging
│   └── ui/
│       ├── app.py              # Root CTk window, sidebar navigation, view router
│       ├── theme.py            # Slate design tokens, typography, dark/light styles
│       ├── components/         # StatCard, ToastNotification, ConfirmDialog, PromptDialog
│       └── views/              # Login, Dashboard, Wizard, Calendar, Directory, Staff, etc.
├── tests/                      # Automated pytest suite (15/15 passing)
├── build_installer.py          # PyInstaller packaging automation script
├── requirements.txt            # Python dependencies
├── main.py                     # Application entry point
└── README.md                   # Documentation
```

---

## 4. Quick Start & Installation

### Step 1: Create Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run Database Migrations
```powershell
alembic upgrade head
```

### Step 4: Launch Application
```powershell
python main.py
```

---

## 5. Demo Credentials

The database comes pre-seeded with realistic demonstration accounts. You can click any role pill on the login screen for instant authentication:

| Role | Username | Password | Access Privileges |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Full system access, users, settings, backups, logs |
| **Practice Owner** | `eleanor` | `owner123` | Full access to appointments, staff, services, reports, settings |
| **Specialist Staff**| `marcus` | `staff123` | Dashboard, calendar, booking wizard, appointments, clients |

---

## 6. Running Automated Tests

Run the full pytest suite with coverage analysis:

```powershell
.\.venv\Scripts\pytest.exe -v --cov=src
```

All 15 automated test cases verify:
- Security, bcrypt hashing, and RBAC permissions
- Availability calculations, working hours, break exclusion, and leave blocking
- Concurrency-safe double-booking prevention
- Rescheduling, cancellation, and slot freeing
- PDF, Excel, and CSV report file generation
- Database backup snapshot creation and SHA256 verification
- Complete UI lifecycle and view routing without memory leaks or detached instance errors

---

## 7. Packaging Windows Executable

To generate a standalone Windows desktop executable using PyInstaller:

```powershell
python build_installer.py
```

The resulting standalone distribution will be generated in `dist/BookEase/BookEase.exe`.
