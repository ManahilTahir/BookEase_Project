"""Data access layer for the BookEase Streamlit app.

This module mirrors the Flask web routes' data-access and business logic
but returns plain Python dicts/lists instead of JSON responses.  It reuses
all existing ``src/`` backend code (models, availability engine, booking
service, security, audit logger) so both the desktop app and the Streamlit
app share the same secure database and business rules.

No Streamlit import here — keeps the layer unit-testable without Streamlit.
"""

import re
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import joinedload

from src.database.connection import get_db
from src.database.models import (
    Service,
    Staff,
    Appointment,
    Customer,
    BusinessSetting,
    StaffSchedule,
    ServiceOption,
    User,
)
from src.core.availability import AvailabilityEngine, time_to_minutes, minutes_to_time
from src.core.booking_service import BookingService
from src.core.audit_logger import AuditLogger
from src.core.security import verify_password

logger = logging.getLogger("bookease.streamlit.db")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sanitize_phone(phone: str) -> str:
    return re.sub(r"[^\d+\-\(\)\s]", "", phone).strip()


def _sanitize_text(text: str, max_len: int = 500) -> str:
    return str(text).strip()[:max_len] if text else ""


def get_settings() -> Dict[str, str]:
    with get_db() as session:
        rows = session.query(BusinessSetting).all()
        return {r.key: r.value for r in rows}


# ── Home page ──────────────────────────────────────────────────────────────────

def get_home_data() -> Dict[str, Any]:
    """Return categories (grouped services) and staff list for the homepage."""
    with get_db() as session:
        services = (
            session.query(Service)
            .filter(Service.is_active == True)
            .order_by(Service.category, Service.name)
            .all()
        )
        staff_list = (
            session.query(Staff)
            .options(joinedload(Staff.services))
            .filter(Staff.is_active == True)
            .order_by(Staff.name)
            .all()
        )
        categories: Dict[str, List[dict]] = {}
        for svc in services:
            cat = svc.category or "General"
            categories.setdefault(cat, []).append({
                "id": svc.id,
                "name": svc.name,
                "description": svc.description or "",
                "duration_minutes": svc.duration_minutes,
                "price": svc.price,
            })
        staff_data = [
            {
                "id": st.id,
                "name": st.name,
                "role_title": st.role_title,
                "specialties": st.specialties or "",
                "bio": st.bio or "",
                "color_code": st.color_code,
                "services": [{"id": s.id, "name": s.name} for s in st.services if s.is_active],
            }
            for st in staff_list
        ]
    return {"categories": categories, "staff_list": staff_data}


# ── Services page ──────────────────────────────────────────────────────────────

def get_services_with_specialists() -> List[dict]:
    with get_db() as session:
        services = (
            session.query(Service)
            .options(joinedload(Service.staff_members))
            .filter(Service.is_active == True)
            .order_by(Service.category, Service.name)
            .all()
        )
        return [
            {
                "id": svc.id,
                "name": svc.name,
                "category": svc.category,
                "description": svc.description or "",
                "duration_minutes": svc.duration_minutes,
                "price": svc.price,
                "specialists": [
                    {"id": st.id, "name": st.name, "role_title": st.role_title}
                    for st in svc.staff_members if st.is_active
                ],
            }
            for svc in services
        ]


# ── Specialists page ───────────────────────────────────────────────────────────

def get_specialists_with_services() -> List[dict]:
    with get_db() as session:
        staff_list = (
            session.query(Staff)
            .options(joinedload(Staff.services))
            .filter(Staff.is_active == True)
            .order_by(Staff.name)
            .all()
        )
        return [
            {
                "id": st.id,
                "name": st.name,
                "role_title": st.role_title,
                "specialties": st.specialties or "",
                "bio": st.bio or "",
                "color_code": st.color_code,
                "services": [
                    {"id": s.id, "name": s.name, "price": s.price, "duration_minutes": s.duration_minutes}
                    for s in st.services if s.is_active
                ],
            }
            for st in staff_list
        ]


# ── Booking wizard data ────────────────────────────────────────────────────────

def get_services_with_options() -> List[dict]:
    """Services with duration/price options for the booking wizard."""
    with get_db() as session:
        services = (
            session.query(Service)
            .options(joinedload(Service.options))
            .filter(Service.is_active == True)
            .order_by(Service.category, Service.name)
            .all()
        )
        return [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "duration_minutes": s.duration_minutes,
                "price": s.price,
                "description": s.description or "",
                "options": [
                    {
                        "id": o.id,
                        "label": o.label or f"{o.duration_minutes} min",
                        "duration_minutes": o.duration_minutes,
                        "price": float(o.price),
                    }
                    for o in s.options if o.is_active
                ],
            }
            for s in services
        ]


def get_staff_for_service(service_id: int) -> List[dict]:
    with get_db() as session:
        staff_list = (
            session.query(Staff)
            .options(joinedload(Staff.services))
            .filter(Staff.is_active == True)
            .join(Staff.services)
            .filter(Service.id == service_id, Service.is_active == True)
            .order_by(Staff.name)
            .all()
        )
        return [
            {
                "id": st.id,
                "name": st.name,
                "role_title": st.role_title,
                "specialties": st.specialties or "",
                "color_code": st.color_code,
            }
            for st in staff_list
        ]


# ── Availability ───────────────────────────────────────────────────────────────

def get_available_slots(
    staff_id: int,
    service_id: int,
    target_date: str,
    duration: Optional[int] = None,
) -> List[dict]:
    try:
        parsed = date.fromisoformat(target_date)
    except ValueError:
        return []
    if parsed < date.today():
        return []
    if parsed > date.today() + timedelta(days=90):
        return []
    with get_db() as session:
        return AvailabilityEngine.get_available_slots(
            session=session,
            staff_id=staff_id,
            service_id=service_id,
            target_date=target_date,
            duration_override=duration if duration and duration > 0 else None,
        )


def get_available_dates(staff_id: int, service_id: int, days: int = 30) -> List[str]:
    available = []
    today = date.today()
    with get_db() as session:
        for i in range(1, days + 1):
            check = today + timedelta(days=i)
            slots = AvailabilityEngine.get_available_slots(
                session=session,
                staff_id=staff_id,
                service_id=service_id,
                target_date=check.isoformat(),
            )
            if slots:
                available.append(check.isoformat())
    return available


# ── Booking creation ───────────────────────────────────────────────────────────

def create_booking(payload: dict, source: str = "Streamlit") -> Tuple[bool, Optional[str], str]:
    """Create a customer booking with full server-side validation.

    Returns ``(success, booking_reference, error_message)``.
    Mirrors the Flask ``/api/book`` endpoint logic exactly.
    """
    required = ["service_id", "staff_id", "date", "start_time", "customer_name", "customer_phone"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return False, None, f"Missing required fields: {', '.join(missing)}"

    service_id = int(payload["service_id"])
    staff_id = int(payload["staff_id"])
    booking_date = _sanitize_text(payload["date"], 10)
    start_time = _sanitize_text(payload["start_time"], 5)
    customer_name = _sanitize_text(payload["customer_name"], 100)
    customer_phone = _sanitize_phone(payload.get("customer_phone", ""))
    customer_email = _sanitize_text(payload.get("customer_email", ""), 100)
    notes = _sanitize_text(payload.get("notes", ""), 500)

    if len(customer_name) < 2:
        return False, None, "Please enter your full name (at least 2 characters)"
    if len(customer_phone) < 7:
        return False, None, "Please enter a valid phone number"
    if customer_email:
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", customer_email):
            return False, None, "Please enter a valid email address"
    try:
        parsed_date = date.fromisoformat(booking_date)
        if parsed_date < date.today():
            return False, None, "Booking date cannot be in the past"
    except ValueError:
        return False, None, "Invalid date format"
    if not re.match(r"^\d{2}:\d{2}$", start_time):
        return False, None, "Invalid time format"

    with get_db() as session:
        service = session.query(Service).filter(Service.id == service_id, Service.is_active == True).first()
        if not service:
            return False, None, "Selected service is not available"
        staff = session.query(Staff).filter(Staff.id == staff_id, Staff.is_active == True).first()
        if not staff:
            return False, None, "Selected specialist is not available"

        custom_price = None
        end_time = None
        option_id = payload.get("option_id")
        if option_id is not None:
            try:
                option_id = int(option_id)
            except (TypeError, ValueError):
                option_id = None
        if option_id:
            option = (
                session.query(ServiceOption)
                .filter(
                    ServiceOption.id == option_id,
                    ServiceOption.service_id == service_id,
                    ServiceOption.is_active == True,
                )
                .first()
            )
            if not option:
                return False, None, "Selected duration option is not available"
            custom_price = option.price
            end_time = minutes_to_time(time_to_minutes(start_time) + option.duration_minutes)

        customer = session.query(Customer).filter(Customer.phone == customer_phone).first()
        if customer:
            if customer_name and customer_name != customer.name:
                customer.name = customer_name
            if customer_email and not customer.email:
                customer.email = customer_email
        else:
            customer = Customer(
                name=customer_name,
                phone=customer_phone,
                email=customer_email or None,
                notes=notes or None,
                total_bookings=0,
            )
            session.add(customer)
            session.flush()

        success, appointment, error_msg = BookingService.create_appointment(
            session=session,
            customer_id=customer.id,
            staff_id=staff_id,
            service_id=service_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            notes=notes or None,
            custom_price=custom_price,
        )
        if not success:
            return False, None, error_msg

        AuditLogger.log(
            session,
            action="WEB_BOOKING",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            details=f"Streamlit booking {appointment.appointment_number} by {customer_name} ({customer_phone})",
            source=source,
        )
        ref = appointment.appointment_number

    logger.info("Streamlit booking created: %s", ref)
    return True, ref, ""


# ── Confirmation ───────────────────────────────────────────────────────────────

def get_confirmation_data(ref: str) -> Optional[dict]:
    ref_clean = _sanitize_text(ref, 30)
    with get_db() as session:
        appt = (
            session.query(Appointment)
            .options(
                joinedload(Appointment.customer),
                joinedload(Appointment.staff),
                joinedload(Appointment.service),
            )
            .filter(Appointment.appointment_number == ref_clean)
            .first()
        )
        if not appt:
            return None
        return {
            "appointment_number": appt.appointment_number,
            "date": appt.date,
            "start_time": appt.start_time,
            "end_time": appt.end_time,
            "status": appt.status,
            "price": appt.price,
            "notes": appt.notes or "",
            "customer_name": appt.customer.name,
            "customer_phone": appt.customer.phone,
            "customer_email": appt.customer.email or "",
            "staff_name": appt.staff.name,
            "staff_role": appt.staff.role_title,
            "service_name": appt.service.name,
            "service_duration": appt.service.duration_minutes,
        }


# ── Internal auth ──────────────────────────────────────────────────────────────

def authenticate_internal(username: str, password: str) -> Tuple[bool, Optional[dict], str]:
    """Authenticate a staff/admin user.

    Returns ``(success, user_dict, error_message)``.
    """
    username = str(username).strip()[:50]
    if not username or not password:
        return False, None, "Username and password are required"
    with get_db() as session:
        user = session.query(User).filter(User.username == username, User.is_active == True).first()
        if not user or not verify_password(password, user.password_hash):
            return False, None, "Invalid username or password"
        return True, {
            "id": user.id,
            "full_name": user.full_name,
            "role": user.role,
            "username": user.username,
        }, ""


# ── Dashboard data ─────────────────────────────────────────────────────────────

def get_dashboard_summary() -> dict:
    """Lightweight summary for the internal dashboard."""
    with get_db() as session:
        from src.core.booking_service import BookingService as BS
        metrics = BS.get_dashboard_metrics(session)
        return metrics