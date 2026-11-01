# BookEase — Professional Universal Booking Agent

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-0F172A?logo=windowsterminal&logoColor=white)](https://customtkinter.tomschimansky.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20SQLAlchemy%20%7C%20Alembic-003B57?logo=sqlite&logoColor=white)](https://www.sqlalchemy.org/)
[![Reports](https://img.shields.io/badge/Reports-ReportLab%20%7C%20openpyxl%20%7C%20Matplotlib-E11D48)](https://www.reportlab.com/)
[![Tests](https://img.shields.io/badge/Tests-42%2F42%20Passing%20(pytest)-10B981?logo=pytest&logoColor=white)](https://docs.pytest.org/)

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
---

## 8. Public Web Portal — Customer Booking Website

BookEase ships a **customer-facing web portal** (Flask) alongside the desktop app. Both share one secure SQLite backend and the same appointment data, so bookings made online appear instantly in the desktop dashboard.

### What customers can do (no install, no account required)
- Browse active services (price, duration, description) and specialist profiles.
- Pick a service + specialist, view **real availability** for a date, and select a time slot.
- Enter name, phone, optional email/notes and confirm — receiving a unique booking reference.
- Open the site on any phone, tablet, laptop, or desktop browser.

### Marketing & PWA readiness
- SEO meta tags, Open Graph, Twitter Cards, `robots.txt`, and `sitemap.xml` (dynamic).
- Installable **Progressive Web App** (`manifest.json` + service worker) — add to phone home screen. Booking works without installing.
- Direct links: `/book?service_id=N`, `/book?staff_id=N`, `/services`, `/specialists`.
- Dark burgundy + pink brand identity, mobile-first responsive CSS, sticky bottom "Book Now" button on mobile.

### Security
- Public routes are read-only + booking; internal Staff/Admin/Owner routes live under `/internal/*` behind authentication and server-side RBAC.
- Server-side validation on every booking; double-booking prevented via the concurrency-safe `BookingService`.
- Rate limiting on the public booking endpoint; database credentials/local DB files are never exposed to the browser.

### Run the web server (development)
```powershell
.\.venv\Scripts\activate
pip install -r web_requirements.txt
python web_server.py
```
Then open **http://localhost:5000** in your browser. The desktop app (`python main.py`) can run simultaneously against the same database.

### Internal staff login (web)
Visit **/internal/login** and use the demo credentials below. Full management features remain in the desktop app; the web portal is customer-facing.

---

## 9. Deployment Guide (Public Hosting)

The portal is a standard WSGI app (`gunicorn web_server:app`) with a `Procfile` and `runtime.txt`, ready for platforms such as **Render**, **Railway**, **Fly.io**, or **Heroku**.

### Option A — Render (recommended, free tier available)
1. Push this repository to GitHub.
2. On Render, create a new **Web Service** and connect the repo.
3. Set the following:
   - **Runtime:** Python 3.13
   - **Build Command:** `pip install -r web_requirements.txt`
   - **Start Command:** `gunicorn web_server:app --timeout 120 --workers 2 --bind 0.0.0.0:$PORT`
4. Add environment variable `BOOKEASE_SECRET_KEY` with a strong random value, and `FLASK_ENV=production`.
5. Deploy. Render assigns a public HTTPS URL automatically.

### Option B — Railway / Fly.io
Use the included `Procfile` and `runtime.txt` (or `Dockerfile` if you add one). Set the same env vars and start command as above.

### Production environment variables
| Variable | Purpose |
|---|---|
| `BOOKEASE_SECRET_KEY` | Flask session signing key (use a long random string) |
| `FLASK_ENV` | Set to `production` to enable secure cookies |
| `HOST` / `PORT` | Bind address (platform usually injects `PORT`) |

> **Note on the database:** SQLite (`data/bookease.db`) is bundled for simplicity. For a durable public deployment, attach a persistent disk to the `data/` directory so bookings survive redeployments. For higher traffic, swap the `DATABASE_URL` in `src/config.py` to PostgreSQL.

---

## 10. Custom Domain

After deploying (e.g. on Render):
1. In your hosting dashboard, open the service → **Settings → Custom Domains**.
2. Add your domain (e.g. `book.yourbusiness.com`).
3. At your DNS provider, create a **CNAME** record pointing `book` → the hosting platform's assigned hostname (Render/Railway show the exact target).
4. Wait for DNS to propagate; the platform provisions a free TLS certificate automatically (HTTPS).
5. Update `business_name`, `phone`, `email`, and `address` in the desktop app's **Settings** (or `BusinessSetting` rows) so the website footer and SEO metadata reflect your real business details.

---

## 11. Testing on a Real Mobile Phone

### Quick local test (same network)
1. Start the server bound to your LAN: `python web_server.py` (ensure `HOST=0.0.0.0`).
2. Find your PC's LAN IP (e.g. `192.168.1.50`).
3. On your phone (same Wi-Fi), open `http://192.168.1.50:5000`.
4. Walk through: Home → Services → pick a service → pick a specialist → choose date/time → enter details → confirm. Verify no horizontal scrolling and the sticky "Book Now" button appears on mobile.

### Responsive viewport testing (desktop browser)
In Chrome/Edge DevTools (F12 → device toolbar), test these widths:
- **320 px** and **375 px** (narrow phones) — single-column cards, hamburger menu, sticky CTA.
- **768 px** (tablet) — grids expand, sticky CTA hides.
- **1024 px+** (desktop) — full hero, multi-column layouts.

### Automated tests
```powershell
.\.venv\Scripts\pytest.exe -v
```
42 tests cover security/RBAC, availability, double-booking prevention, report generation, backups, the desktop UI lifecycle, **and** the web portal (routes, booking API, conflicts, internal auth, rate limiting).
