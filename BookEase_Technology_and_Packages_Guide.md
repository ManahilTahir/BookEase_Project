# BookEase — Technology and Packages Guide

**Project:** BookEase — Professional Universal Booking Management v1.0.0  
**Business:** Lumière Wellness & Spa  
**Python Version:** 3.13.0  
**Platform:** Windows 11 (desktop app), Web (Streamlit + Flask)

A beginner-friendly guide to every technology and package used in the BookEase project, based entirely on the actual source code and `requirements.txt`.

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Packages — Complete List](#2-packages--complete-list)
3. [Code Examples](#3-code-examples)
4. [Project Architecture](#4-project-architecture)
5. [Setup Guide](#5-setup-guide)
6. [Dependencies Analysis](#6-dependencies-analysis)

---

## 1. Technology Stack

BookEase is built as a **dual-frontend, shared-backend** system. Two user interfaces (a desktop app and a web app) share the same business logic and database.

### Stack Overview

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.13 | All application code |
| **Desktop UI** | CustomTkinter (Tkinter) | Staff/admin/owner management interface |
| **Web UI (Customer)** | Streamlit | Customer-facing booking website |
| **Web UI (Legacy/API)** | Flask + Flask-Session | Internal staff web portal and REST API |
| **Database** | SQLite (WAL mode) | Central data store (`data/bookease.db`) |
| **ORM** | SQLAlchemy 2.x | Database models, queries, sessions |
| **Migrations** | Alembic | Schema versioning and migrations |
| **Authentication** | bcrypt | Password hashing and verification |
| **Charts** | Matplotlib | Dashboard and report graphs |
| **Data Analysis** | Pandas + NumPy | Report data processing |
| **PDF Reports** | ReportLab | Professional PDF export |
| **Excel Reports** | openpyxl | Formatted Excel export |
| **Image Processing** | Pillow (PIL) | Icon generation |
| **Testing** | pytest + pytest-cov | Unit tests and coverage |
| **Packaging** | PyInstaller | Windows .exe builder |
| **WSGI Server** | Gunicorn | Production web server (deployment) |

### How the Pieces Fit Together

```
┌─────────────────────┐    ┌─────────────────────┐
│  Desktop App        │    │  Streamlit Website  │
│  (CustomTkinter)    │    │  (Customer Portal)  │
│  main.py            │    │  streamlit_app.py   │
└────────┬────────────┘    └────────┬────────────┘
         │                          │
         │    ┌─────────────────────┘
         │    │
         ▼    ▼
┌─────────────────────────────────────┐
│  Shared Business Logic (src/core/)  │
│  • BookingService                   │
│  • AvailabilityEngine               │
│  • Security / RBAC                  │
│  • ReportsService                   │
│  • AuditLogger                      │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Data Access Layer (src/database/)  │
│  SQLAlchemy ORM → SQLite            │
│  data/bookease.db (WAL mode)        │
└─────────────────────────────────────┘
```

---

## 2. Packages — Complete List

### 2.1 Direct Dependencies (from `requirements.txt`)

These 20 packages are explicitly listed in `requirements.txt`:

| # | Package | Version | Purpose | Where Used |
|---|---------|---------|---------|------------|
| 1 | **customtkinter** | 6.0.0 | Modern themed Tkinter widgets for the desktop UI | `src/ui/app.py`, all views in `src/ui/views/`, `src/ui/components/` |
| 2 | **pillow** (PIL) | 12.3.0 | Image creation and processing | `generate_icons.py` (app icon generation) |
| 3 | **tkcalendar** | 1.6.1 | Calendar date-picker widget | *Listed but not imported in source — see Dependencies section* |
| 4 | **babel** | 2.18.0 | Internationalization and localization | *Listed but not imported in source — bundled by PyInstaller* |
| 5 | **sqlalchemy** | 2.1.4 | SQL ORM — models, queries, sessions, relationships | `src/database/models.py`, `src/database/connection.py`, all `src/core/` services, `streamlit_app/db.py` |
| 6 | **alembic** | 1.20.0 | Database schema migrations | `alembic/` directory, `alembic.ini` |
| 7 | **bcrypt** | 5.0.0 | Secure password hashing (bcrypt algorithm) | `src/core/security.py` |
| 8 | **pydantic** | 2.14.0 | Data validation using Python type hints | *Listed but not imported in source — see Dependencies section* |
| 9 | **pandas** | 3.0.6 | Data analysis and manipulation (DataFrames) | `src/ui/views/reports_view.py` |
| 10 | **numpy** | 2.5.3 | Numerical computing (arrays, math) | `src/ui/views/reports_view.py` |
| 11 | **matplotlib** | 3.11.2 | Charts and graphs (revenue, occupancy) | `src/ui/views/dashboard_view.py`, `src/ui/views/reports_view.py` |
| 12 | **reportlab** | 5.0.1 | PDF document generation | `src/core/reports_service.py` |
| 13 | **openpyxl** | 3.1.5 | Excel (.xlsx) file generation with styling | `src/core/reports_service.py` |
| 14 | **pytest** | 9.1.1 | Testing framework | `tests/` (87 tests) |
| 15 | **pytest-cov** | 7.1.0 | Test coverage measurement | Used with pytest |
| 16 | **pyinstaller** | 6.22.3 | Freeze Python app into a standalone .exe | `build_installer.py`, `BookEase.spec` |
| 17 | **streamlit** | *not installed* | Web app framework for the customer booking site | `streamlit_app.py`, `streamlit_app/` package |
| 18 | **flask** | 3.1.3 | Web framework for internal staff portal and API | `web/app.py`, `web/routes/`, `web_server.py` |
| 19 | **flask-session** | 0.8.0 | Server-side session storage for Flask | `web/app.py` |
| 20 | **gunicorn** | 26.2.0 | Production WSGI HTTP server | `Procfile` (deployment) |

> **Note:** `streamlit` is listed in `requirements.txt` but could not be installed in this sandbox environment due to network restrictions. Install it manually with `pip install streamlit`.

### 2.2 Indirect Dependencies (installed automatically)

These packages are installed as dependencies of the direct packages above. They are needed at runtime but are not listed in `requirements.txt`:

| Package | Version | Required By | Purpose |
|---------|---------|-------------|---------|
| altgraph | 0.17.5 | pyinstaller | Graph data structure for dependency analysis |
| annotated-types | 0.8.0 | pydantic | Type annotation support |
| blinker | 1.9.0 | flask | Signal/event system for Flask |
| cachelib | 0.17.0 | flask-session | Filesystem cache backend for sessions |
| charset-normalizer | 3.5.2 | — | Character encoding detection |
| click | 8.5.0 | flask | Command-line interface framework (Flask CLI) |
| colorama | 0.4.6 | click | Colored terminal output on Windows |
| contourpy | 1.4.0 | matplotlib | Contour plot rendering |
| coverage | 7.16.2 | pytest-cov | Code coverage measurement engine |
| cycler | 0.12.1 | matplotlib | Composable cycles for matplotlib |
| darkdetect | 0.8.0 | customtkinter | OS dark/light mode detection |
| et_xmlfile | 2.0.0 | openpyxl | XML file writer for Excel |
| fonttools | 4.66.1 | matplotlib | Font parsing and manipulation |
| hypothesis | 6.168.5 | — | Property-based testing (installed but not used) |
| iniconfig | 2.3.1 | pytest | INI file parsing |
| itsdangerous | 2.2.0 | flask | Signed data serialization (session cookies) |
| Jinja2 | 3.1.6 | flask | HTML template engine |
| kiwisolver | 1.5.1 | matplotlib | Constraint solver for layout |
| Mako | 1.4.3 | alembic | Template engine for migration scripts |
| MarkupSafe | 3.0.4 | Jinja2 | HTML-safe string escaping |
| msgspec | 0.22.0 | — | Fast serialization library |
| packaging | 26.3 | — | Package version parsing |
| pefile | 2024.8.26 | pyinstaller | Windows PE file parsing |
| pluggy | 1.6.0 | pytest | Plugin management for pytest |
| pydantic_core | 2.50.0 | pydantic | Rust core for pydantic validation |
| Pygments | 2.21.0 | pytest | Syntax highlighting |
| pyinstaller-hooks-contrib | 2026.8 | pyinstaller | PyInstaller hooks for common packages |
| pyparsing | 3.3.3 | matplotlib | Parsing library |
| python-dateutil | 2.9.0 | matplotlib | Date/time utilities |
| python-dotenv | 1.2.4 | — | .env file loading (installed but not used) |
| pywin32-ctypes | 0.2.3 | pyinstaller | Windows COM/Win32 access |
| setuptools | 84.0.0 | — | Python package build tool |
| six | 1.17.0 | python-dateutil | Python 2/3 compatibility |
| sortedcontainers | 2.4.0 | — | Sorted collection types |
| typing_extensions | 4.16.0 | — | Backported type hints |
| typing-inspection | 0.4.4 | pydantic | Type inspection utilities |
| tzdata | 2026.5 | — | Timezone database |
| Werkzeug | 3.1.9 | flask | WSGI utility library (Flask foundation) |

---

## 3. Code Examples

### 3.1 SQLAlchemy — Database Models and Sessions

**File:** `src/database/models.py` — defining entities:

```python
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_number = Column(String(30), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    date = Column(String(10), nullable=False)
    start_time = Column(String(5), nullable=False)
    status = Column(String(20), nullable=False, default="confirmed")
    price = Column(Float, nullable=False, default=0.0)

    customer = relationship("Customer", back_populates="appointments")
    staff = relationship("Staff", back_populates="appointments")
```

**File:** `src/database/connection.py` — session management:

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

SessionLocal = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))

@contextmanager
def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        SessionLocal.remove()
```

### 3.2 bcrypt — Password Security

**File:** `src/core/security.py`:

```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False
```

### 3.3 CustomTkinter — Desktop UI

**File:** `src/ui/app.py` — main window:

```python
import customtkinter as ctk

class BookEaseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BookEase — Professional Universal Booking Agent v1.0.0")
        self.geometry("1280x820")
        self.minsize(1050, 700)

        self.main_container = ctk.CTkFrame(self, fg_color="#0F172A")
        self.main_container.pack(fill="both", expand=True)

        if not SessionManager.is_authenticated():
            self.show_login()
```

### 3.4 Streamlit — Customer Website

**File:** `streamlit_app.py` — entry point:

```python
import streamlit as st

def main():
    st.set_page_config(
        page_title="BookEase — Book Online",
        page_icon="✦",
        layout="wide",
    )

    if "be_db_initialized" not in st.session_state:
        init_db()
        st.session_state.be_db_initialized = True

    page = st.query_params.get("page", "home")

    if page == "home":
        from streamlit_app.pages.home import render
    elif page == "book":
        from streamlit_app.pages.book import render

    render()
```

### 3.5 Flask — Internal Web Portal

**File:** `web/app.py` — app factory:

```python
from flask import Flask, render_template, jsonify
from flask_session import Session

def create_app(config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config)

    app.config.setdefault("SESSION_TYPE", "filesystem")
    Session(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(internal_bp)
    return app
```

### 3.6 Matplotlib — Dashboard Charts

**File:** `src/ui/views/dashboard_view.py`:

```python
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

fig = Figure(figsize=(6, 3), dpi=100)
ax = fig.add_subplot(111)
ax.bar(["Mon", "Tue", "Wed", "Thu", "Fri"], revenue_data)
ax.set_title("Weekly Revenue")

canvas = FigureCanvasTkAgg(fig, master=parent_frame)
canvas.draw()
canvas.get_tk_widget().pack(fill="both", expand=True)
```

### 3.7 Pandas + NumPy — Report Data

**File:** `src/ui/views/reports_view.py`:

```python
import pandas as pd
import numpy as np

df = pd.DataFrame(appointments_data, columns=["date", "price", "status"])
revenue_by_day = df.groupby("date")["price"].sum()
avg_revenue = np.mean(revenue_by_day.values)
```

### 3.8 ReportLab — PDF Export

**File:** `src/core/reports_service.py`:

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle

doc = SimpleDocTemplate(str(output_path), pagesize=letter)
elements = []
elements.append(Paragraph("Appointments Report", title_style))
table = Table(data, colWidths=[75, 75, 100, 85, 110, 55, 50])
table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9"))]))
elements.append(table)
doc.build(elements)
```

### 3.9 openpyxl — Excel Export

**File:** `src/core/reports_service.py`:

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Appointments"

ws["A1"] = "Lumière Wellness & Spa"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="1E3A8A")

for col_idx, header in enumerate(headers, 1):
    cell = ws.cell(row=4, column=col_idx, value=header)
    cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")

wb.save(output_path)
```

### 3.10 PyInstaller — Building the .exe

**File:** `build_installer.py`:

```python
cmd = [
    str(pyinstaller_exe),
    "--noconfirm", "--onedir", "--windowed",
    "--name", "BookEase",
    "--collect-all", "customtkinter",
    "--collect-all", "reportlab",
    "--hidden-import", "sqlalchemy.dialects.sqlite",
    "--add-data", f"{assets_dir};assets",
    str(BASE_DIR / "main.py"),
]
subprocess.run(cmd)
```

### 3.11 Pillow — Icon Generation

**File:** `generate_icons.py`:

```python
from PIL import Image, ImageDraw, ImageFont

img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.rounded_rectangle([20, 20, 236, 236], radius=40, fill="#C4627A")
img.save("assets/icon_256.png")
```

---

## 4. Project Architecture

### 4.1 Two Frontends, One Backend

BookEase has **two user interfaces** that serve different audiences:

| Interface | Entry Point | Audience | Technology |
|-----------|------------|----------|------------|
| **Desktop App** | `main.py` | Staff, Admin, Owner (internal) | CustomTkinter |
| **Streamlit Website** | `streamlit_app.py` | Customers (public) | Streamlit |
| **Flask Web Portal** | `web_server.py` | Staff API (legacy/deployment) | Flask + Flask-Session |

All three share the **same backend** (`src/core/`) and the **same database** (`data/bookease.db`).

### 4.2 Desktop Application (CustomTkinter)

The desktop app is for internal staff to manage the business. It has **11 views**:

| View | File | Purpose |
|------|------|---------|
| Login | `login_view.py` | Username/password authentication |
| Dashboard | `dashboard_view.py` | Overview stats and revenue charts |
| Booking Wizard | `booking_wizard.py` | Step-by-step appointment creation |
| Calendar | `calendar_view.py` | Visual calendar of appointments |
| Appointments | `appointments_view.py` | List, filter, update appointment status |
| Customers | `customers_view.py` | Customer profiles and history |
| Staff | `staff_view.py` | Manage staff, schedules, leaves |
| Services | `services_view.py` | Manage services and pricing options |
| Reports | `reports_view.py` | Generate PDF/Excel/CSV reports with charts |
| Settings | `settings_view.py` | Business configuration |
| Customer Booking | `customer_booking_view.py` | Walk-in booking at the front desk |

### 4.3 Streamlit Customer Website

The Streamlit app is the public booking site. It has **7 pages**:

| Page | File | Purpose |
|------|------|---------|
| Home | `home.py` | Landing page with services and specialists |
| Services | `services.py` | Browse all services with pricing |
| Specialists | `specialists.py` | Browse staff profiles |
| Book | `book.py` | Multi-step booking form |
| Confirmation | `confirmation.py` | Booking confirmation with reference number |
| Login | `login.py` | Staff login for dashboard access |
| Dashboard | `dashboard.py` | Internal dashboard (authenticated) |

### 4.4 Shared Business Logic (`src/core/`)

| Module | Class | Responsibility |
|--------|-------|----------------|
| `security.py` | `SessionManager` | Authentication, RBAC permission checks |
| `booking_service.py` | `BookingService` | Create, reschedule, cancel appointments |
| `availability.py` | `AvailabilityEngine` | Compute free time slots from schedules |
| `reports_service.py` | `ReportsService` | Export CSV, Excel, PDF reports |
| `backup_manager.py` | `BackupManager` | Database backup and restore |
| `audit_logger.py` | `AuditLogger` | Audit trail for all sensitive actions |
| `notifications.py` | `NotificationService` | Email confirmations via SMTP |

### 4.5 Database (`src/database/`)

| Module | Purpose |
|--------|---------|
| `models.py` | 10 SQLAlchemy entities + 1 association table |
| `connection.py` | Engine, session factory, `get_db()` context manager |
| `seed_data.py` | Initial data (admin user, services, staff, settings) |

**Entities:** User, Staff, Service, ServiceOption, StaffSchedule, StaffLeave, Customer, Appointment, BusinessSetting, AuditLog

### 4.6 User Roles and Permissions

Three roles with different permission levels:

| Permission | Admin | Owner | Staff |
|-----------|-------|-------|-------|
| View dashboard | ✅ | ✅ | ✅ |
| Manage appointments | ✅ | ✅ | ✅ |
| View calendar | ✅ | ✅ | ✅ |
| Manage customers | ✅ | ✅ | ✅ |
| Manage staff | ✅ | ✅ | ❌ |
| Manage services | ✅ | ✅ | ❌ |
| View reports | ✅ | ✅ | ❌ |
| Export data | ✅ | ✅ | ❌ |
| Manage settings | ✅ | ✅ | ❌ |
| Manage users | ✅ | ❌ | ❌ |
| Manage backups | ✅ | ✅ | ❌ |
| View audit logs | ✅ | ✅ | ❌ |

### 4.7 How Data Stays in Sync

Both apps read and write to the **same SQLite database file** (`data/bookease.db`). SQLite is configured with:

- **WAL mode** (`PRAGMA journal_mode=WAL`) — allows concurrent reads while writing
- **busy_timeout=5000ms** — waits up to 5 seconds if the database is locked
- **Foreign keys ON** — enforces referential integrity

This means a booking made on the Streamlit website is **instantly visible** in the desktop app — no sync process needed.

---

## 5. Setup Guide

### 5.1 Prerequisites

- **Python 3.13** (or 3.10+)
- **Windows 10/11** (for the desktop app; Streamlit works on any OS)
- **pip** (comes with Python)

### 5.2 Step 1 — Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 5.3 Step 2 — Install All Packages

```powershell
pip install -r requirements.txt
```

This installs all 20 direct dependencies. Indirect dependencies are installed automatically.

> If `streamlit` fails to install due to network issues, install it separately:
> ```powershell
> pip install streamlit
> ```

### 5.4 Step 3 — Run the Desktop Application (Staff/Admin/Owner)

```powershell
.\.venv\Scripts\python.exe main.py
```

This opens the CustomTkinter desktop window. On first run, the database is automatically created and seeded with initial data (admin user, sample services, staff).

**Default admin login:**
- Username: `admin`
- Password: `admin123`

### 5.5 Step 4 — Run the Streamlit Customer Website

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

This starts a local web server at `http://localhost:8501`. Customers can browse services and book appointments.

### 5.6 Step 5 — Run the Flask Web Server (Optional)

```powershell
.\.venv\Scripts\python.exe web_server.py
```

This starts the Flask internal portal at `http://localhost:5000`.

### 5.7 Step 6 — Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

All 87 tests should pass.

### 5.8 Step 7 — Build a Windows Installer (.exe)

```powershell
.\.venv\Scripts\python.exe build_installer.py
```

The standalone executable is output to `dist/BookEase/BookEase.exe`.

### 5.9 Deployment Requirements

#### Streamlit Community Cloud (recommended for the customer website)

1. Push the repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select the repo and set the entry point to `streamlit_app.py`
4. The `Procfile` and `.streamlit/config.toml` are already configured

**Procfile:**
```
web: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

**runtime.txt:**
```
python-3.13.0
```

#### Traditional Server (with Gunicorn for Flask)

```powershell
gunicorn web_server:app --bind 0.0.0.0:5000
```

#### Desktop App Distribution

Use PyInstaller to create a standalone `.exe` that doesn't require Python:

```powershell
.\.venv\Scripts\python.exe build_installer.py
```

---

## 6. Dependencies Analysis

### 6.1 Direct Dependencies

These are the 20 packages explicitly listed in `requirements.txt`. They are intentionally chosen for the project:

| Package | Status | Notes |
|---------|--------|-------|
| customtkinter | ✅ Active | Core desktop UI framework |
| pillow | ✅ Active | Used in `generate_icons.py` for icon creation |
| sqlalchemy | ✅ Active | Core ORM — used everywhere |
| alembic | ✅ Active | Database migrations (`alembic/` directory) |
| bcrypt | ✅ Active | Password security |
| pandas | ✅ Active | Report data processing |
| numpy | ✅ Active | Numerical operations in reports |
| matplotlib | ✅ Active | Dashboard and report charts |
| reportlab | ✅ Active | PDF report generation |
| openpyxl | ✅ Active | Excel report generation |
| pytest | ✅ Active | Testing framework (87 tests) |
| pytest-cov | ✅ Active | Test coverage reporting |
| pyinstaller | ✅ Active | Windows .exe packaging |
| streamlit | ⚠️ Not installed | Customer website framework — install manually |
| flask | ✅ Active | Internal web portal and API |
| flask-session | ✅ Active | Server-side session storage |
| gunicorn | ✅ Active | Production WSGI server |

### 6.2 Indirect Dependencies

These 37 packages are installed automatically as dependencies of the direct packages. They are required at runtime but are not listed in `requirements.txt`:

| Required By | Packages |
|-------------|----------|
| **flask** | blinker, click, itsdangerous, Jinja2, MarkupSafe, Werkzeug, colorama |
| **flask-session** | cachelib |
| **customtkinter** | darkdetect |
| **matplotlib** | contourpy, cycler, fonttools, kiwisolver, pyparsing, python-dateutil |
| **python-dateutil** | six |
| **openpyxl** | et_xmlfile |
| **pydantic** | annotated-types, pydantic_core, typing-inspection |
| **pytest** | iniconfig, pluggy, Pygments |
| **pytest-cov** | coverage |
| **pyinstaller** | altgraph, pefile, pyinstaller-hooks-contrib, pywin32-ctypes |
| **alembic** | Mako |
| **General** | charset-normalizer, msgspec, packaging, python-dotenv, setuptools, sortedcontainers, typing_extensions, tzdata, hypothesis |

### 6.3 Unused Packages

These packages are listed in `requirements.txt` but are **not imported anywhere** in the project source code:

| Package | In `requirements.txt` | Reason for Inclusion |
|---------|----------------------|---------------------|
| **tkcalendar** | `tkcalendar>=1.6.1` | Likely planned for a calendar date-picker widget but never integrated. The project uses its own calendar view (`calendar_view.py`) built with CustomTkinter instead. |
| **babel** | `babel>=2.14.0` | Internationalization library. Not imported in source code, but is bundled by PyInstaller (`build_installer.py` line 34: `"--collect-all", "babel"`). May have been planned for multi-language support. |
| **pydantic** | `pydantic>=2.8.2` | Data validation library. Not imported in any source file. May have been planned for input validation but the project uses manual validation instead. |

> **Recommendation:** These three packages can be safely removed from `requirements.txt` if they are not needed for future features. However, `babel` is currently bundled by the PyInstaller build script, so removing it requires also updating `build_installer.py`.

### 6.4 Duplicate Packages

There are **no duplicate packages** in the project. The former `web_requirements.txt` was merged into `requirements.txt` during the integration phase, creating a single unified requirements file. The file `web_requirements.txt` no longer exists.

**Before (two files):**
- `requirements.txt` — desktop app dependencies
- `web_requirements.txt` — Flask web dependencies

**After (one file):**
- `requirements.txt` — all dependencies (desktop + web + Streamlit + testing + packaging)

### 6.5 Summary Table

| Category | Count | Packages |
|----------|-------|----------|
| **Direct (active)** | 17 | customtkinter, pillow, sqlalchemy, alembic, bcrypt, pandas, numpy, matplotlib, reportlab, openpyxl, pytest, pytest-cov, pyinstaller, flask, flask-session, gunicorn, streamlit |
| **Direct (unused)** | 3 | tkcalendar, babel, pydantic |
| **Indirect** | 37 | Automatically installed dependencies |
| **Duplicate** | 0 | None (unified into single `requirements.txt`) |
| **Total installed** | 57 | All packages in the virtual environment |

---

*This guide is based on the BookEase v1.0.0 codebase. All package versions, usage locations, and code examples reflect the actual implementation as of the current project state.*