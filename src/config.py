"""BookEase Configuration & Constants."""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "bookease.db"
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

REPORTS_DIR = BASE_DIR / "reports_output"
REPORTS_DIR.mkdir(exist_ok=True)

ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# SQLAlchemy Database URI
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# App Information
APP_NAME = "BookEase"
APP_SUBTITLE = "Professional Universal Booking Management"
APP_VERSION = "1.0.0"

# User Roles
ROLE_ADMIN = "admin"
ROLE_OWNER = "owner"
ROLE_STAFF = "staff"

ROLES = [ROLE_ADMIN, ROLE_OWNER, ROLE_STAFF]

# Appointment Statuses
STATUS_CONFIRMED = "confirmed"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
STATUS_NO_SHOW = "no_show"

APPOINTMENT_STATUSES = [
    STATUS_CONFIRMED,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
    STATUS_NO_SHOW,
]

STATUS_COLORS = {
    STATUS_CONFIRMED: "#3B82F6",   # Vibrant Blue
    STATUS_COMPLETED: "#10B981",   # Emerald Green
    STATUS_CANCELLED: "#EF4444",   # Rose Red
    STATUS_NO_SHOW: "#F59E0B",     # Amber Warning
}

# Role Permissions Mapping
ROLE_PERMISSIONS = {
    ROLE_ADMIN: {
        "view_dashboard": True,
        "manage_appointments": True,
        "view_calendar": True,
        "manage_customers": True,
        "manage_staff": True,
        "manage_services": True,
        "view_reports": True,
        "export_data": True,
        "manage_settings": True,
        "manage_users": True,
        "manage_backups": True,
        "view_audit_logs": True,
    },
    ROLE_OWNER: {
        "view_dashboard": True,
        "manage_appointments": True,
        "view_calendar": True,
        "manage_customers": True,
        "manage_staff": True,
        "manage_services": True,
        "view_reports": True,
        "export_data": True,
        "manage_settings": True,
        "manage_users": False,
        "manage_backups": True,
        "view_audit_logs": True,
    },
    ROLE_STAFF: {
        "view_dashboard": True,
        "manage_appointments": True,
        "view_calendar": True,
        "manage_customers": True,
        "manage_staff": False,
        "manage_services": False,
        "view_reports": False,
        "export_data": False,
        "manage_settings": False,
        "manage_users": False,
        "manage_backups": False,
        "view_audit_logs": False,
    },
}

# Default Business Settings
DEFAULT_SETTINGS = {
    "business_name": "Lumière Wellness & Spa",
    "business_category": "Salon & Wellness Spa",
    "owner_name": "Eleanor Vance",
    "phone": "+1 (555) 328-9400",
    "email": "contact@lumierewellness.com",
    "address": "742 Evergreen Terrace, Suite 100",
    "currency_symbol": "$",
    "currency_code": "USD",
    "timezone": "UTC",
    "default_appointment_buffer": "15",  # minutes
    "default_slot_interval": "15",       # minutes
    "auto_confirm_appointments": "true",
    "allow_double_booking": "false",
    "smtp_enabled": "false",
    "smtp_server": "smtp.mailtrap.io",
    "smtp_port": "587",
    "smtp_username": "",
    "smtp_password": "",
    "smtp_from_email": "bookings@lumierewellness.com",
    "color_theme": "emerald",
}

# Day names mapping (0=Monday ... 6=Sunday)
DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
