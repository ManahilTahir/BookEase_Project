"""Public customer-facing API routes for BookEase web portal."""

import re
import logging
from datetime import date, timedelta
from flask import Blueprint, jsonify, request, render_template, abort
from sqlalchemy.orm import joinedload

from src.database.connection import get_db
from src.database.models import (
    Service, Staff, Appointment, Customer, BusinessSetting, StaffSchedule, ServiceOption
)
from src.core.availability import AvailabilityEngine, time_to_minutes, minutes_to_time
from src.core.booking_service import BookingService
from src.core.audit_logger import AuditLogger
from web.rate_limit import booking_limiter

logger = logging.getLogger("bookease.web.public")
public_bp = Blueprint("public", __name__)


def _get_settings(session) -> dict:
    """Load all business settings into a dict."""
    rows = session.query(BusinessSetting).all()
    return {r.key: r.value for r in rows}


def _sanitize_phone(phone: str) -> str:
    """Basic phone normalization."""
    return re.sub(r"[^\d+\-\(\)\s]", "", phone).strip()


def _sanitize_text(text: str, max_len: int = 500) -> str:
    """Strip dangerous chars and limit length."""
    return str(text).strip()[:max_len] if text else ""


@public_bp.route("/")
def index():
    """Homepage — hero, active services grouped by category, active staff."""
    with get_db() as session:
        settings = _get_settings(session)
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
        # Group services by category
        categories = {}
        for svc in services:
            cat = svc.category or "General"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "id": svc.id,
                "name": svc.name,
                "description": svc.description or "",
                "duration_minutes": svc.duration_minutes,
                "price": svc.price,
            })

        staff_data = []
        for st in staff_list:
            staff_data.append({
                "id": st.id,
                "name": st.name,
                "role_title": st.role_title,
                "specialties": st.specialties or "",
                "bio": st.bio or "",
                "color_code": st.color_code,
                "services": [{"id": s.id, "name": s.name} for s in st.services if s.is_active],
            })

    return render_template(
        "index.html",
        settings=settings,
        categories=categories,
        staff_list=staff_data,
        page_title=f"{settings.get('business_name', 'BookEase')} — Book Online",
    )


@public_bp.route("/services")
def services_page():
    """Services listing page."""
    with get_db() as session:
        settings = _get_settings(session)
        services = (
            session.query(Service)
            .options(joinedload(Service.staff_members))
            .filter(Service.is_active == True)
            .order_by(Service.category, Service.name)
            .all()
        )
        services_data = []
        for svc in services:
            services_data.append({
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
            })

    return render_template(
        "services.html",
        settings=settings,
        services=services_data,
        page_title=f"Services — {settings.get('business_name', 'BookEase')}",
    )


@public_bp.route("/specialists")
def specialists_page():
    """Staff/specialist listing page."""
    with get_db() as session:
        settings = _get_settings(session)
        staff_list = (
            session.query(Staff)
            .options(joinedload(Staff.services))
            .filter(Staff.is_active == True)
            .order_by(Staff.name)
            .all()
        )
        staff_data = []
        for st in staff_list:
            staff_data.append({
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
            })

    return render_template(
        "specialists.html",
        settings=settings,
        staff_list=staff_data,
        page_title=f"Our Specialists — {settings.get('business_name', 'BookEase')}",
    )


@public_bp.route("/book")
def book_page():
    """Multi-step booking wizard page."""
    with get_db() as session:
        settings = _get_settings(session)
        services = (
            session.query(Service)
            .options(joinedload(Service.options))
            .filter(Service.is_active == True)
            .order_by(Service.category, Service.name)
            .all()
        )
        services_data = [
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
        # Preselected service/staff from query params
        preselect_service = request.args.get("service_id", type=int)
        preselect_staff = request.args.get("staff_id", type=int)

    today_date = date.today()
    max_date   = today_date + timedelta(days=90)

    return render_template(
        "book.html",
        settings=settings,
        services=services_data,
        preselect_service=preselect_service,
        preselect_staff=preselect_staff,
        today=today_date.isoformat(),
        max_date=max_date.isoformat(),
        page_title=f"Book Appointment — {settings.get('business_name', 'BookEase')}",
    )


@public_bp.route("/confirmation/<string:ref>")
def confirmation_page(ref):
    """Booking confirmation page."""
    ref_clean = _sanitize_text(ref, 30)
    with get_db() as session:
        settings = _get_settings(session)
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
            return render_template(
                "not_found.html",
                settings=settings,
                page_title="Booking Not Found",
                message=f"No booking found with reference {ref_clean}.",
            ), 404

        appt_data = {
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

    return render_template(
        "confirmation.html",
        settings=settings,
        appt=appt_data,
        page_title=f"Booking Confirmed — {ref_clean}",
    )


# ── API Endpoints ──────────────────────────────────────────────────────────────

@public_bp.route("/api/services")
def api_services():
    """Return JSON list of active services."""
    with get_db() as session:
        services = (
            session.query(Service)
            .options(joinedload(Service.staff_members), joinedload(Service.options))
            .filter(Service.is_active == True)
            .order_by(Service.category, Service.name)
            .all()
        )
        data = [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "description": s.description or "",
                "duration_minutes": s.duration_minutes,
                "price": float(s.price),
                "options": [
                    {
                        "id": o.id,
                        "label": o.label or f"{o.duration_minutes} min",
                        "duration_minutes": o.duration_minutes,
                        "price": float(o.price),
                    }
                    for o in s.options if o.is_active
                ],
                "specialists": [
                    {"id": st.id, "name": st.name, "role_title": st.role_title, "color": st.color_code}
                    for st in s.staff_members if st.is_active
                ],
            }
            for s in services
        ]
    return jsonify({"services": data})


@public_bp.route("/api/staff")
def api_staff():
    """Return JSON list of active staff."""
    service_filter = request.args.get("service_id", type=int)
    with get_db() as session:
        query = (
            session.query(Staff)
            .options(joinedload(Staff.services))
            .filter(Staff.is_active == True)
        )
        if service_filter:
            query = query.join(Staff.services).filter(Service.id == service_filter, Service.is_active == True)
        staff_list = query.order_by(Staff.name).all()

        data = [
            {
                "id": st.id,
                "name": st.name,
                "role_title": st.role_title,
                "specialties": st.specialties or "",
                "bio": st.bio or "",
                "color_code": st.color_code,
                "services": [
                    {"id": s.id, "name": s.name, "price": float(s.price)}
                    for s in st.services if s.is_active
                ],
            }
            for st in staff_list
        ]
    return jsonify({"staff": data})


@public_bp.route("/api/slots")
def api_slots():
    """Return available time slots for a given staff+service+date combination."""
    staff_id = request.args.get("staff_id", type=int)
    service_id = request.args.get("service_id", type=int)
    target_date = request.args.get("date", "")
    duration = request.args.get("duration", type=int)

    if not all([staff_id, service_id, target_date]):
        return jsonify({"error": "staff_id, service_id, and date are required"}), 400

    # Validate date format
    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Don't allow past dates
    if parsed_date < date.today():
        return jsonify({"slots": [], "message": "Date is in the past"}), 200

    # Don't allow more than 90 days ahead
    if parsed_date > date.today() + timedelta(days=90):
        return jsonify({"slots": [], "message": "Date too far ahead"}), 200

    with get_db() as session:
        slots = AvailabilityEngine.get_available_slots(
            session=session,
            staff_id=staff_id,
            service_id=service_id,
            target_date=target_date,
            duration_override=duration if duration and duration > 0 else None,
        )

    return jsonify({"slots": slots, "date": target_date, "count": len(slots)})


@public_bp.route("/api/available-dates")
def api_available_dates():
    """Return a list of dates (next 30 days) that have at least one slot for staff+service."""
    staff_id = request.args.get("staff_id", type=int)
    service_id = request.args.get("service_id", type=int)

    if not all([staff_id, service_id]):
        return jsonify({"error": "staff_id and service_id are required"}), 400

    available_dates = []
    today = date.today()

    with get_db() as session:
        for i in range(1, 31):  # Check next 30 days
            check_date = today + timedelta(days=i)
            slots = AvailabilityEngine.get_available_slots(
                session=session,
                staff_id=staff_id,
                service_id=service_id,
                target_date=check_date.isoformat(),
            )
            if slots:
                available_dates.append(check_date.isoformat())

    return jsonify({"available_dates": available_dates})


@public_bp.route("/api/book", methods=["POST"])
@booking_limiter.decorator(limit=5, window=60)
def api_book():
    """
    Create a customer booking. Validates all fields server-side.
    Accepts JSON body:
    {
        "service_id": int,
        "staff_id": int,
        "date": "YYYY-MM-DD",
        "start_time": "HH:MM",
        "customer_name": str,
        "customer_phone": str,
        "customer_email": str (optional),
        "notes": str (optional)
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON body"}), 400

    # ── Validate required fields ──────────────────────────
    required = ["service_id", "staff_id", "date", "start_time", "customer_name", "customer_phone"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "error": f"Missing required fields: {', '.join(missing)}"}), 400

    service_id = int(data["service_id"])
    staff_id = int(data["staff_id"])
    booking_date = _sanitize_text(data["date"], 10)
    start_time = _sanitize_text(data["start_time"], 5)
    customer_name = _sanitize_text(data["customer_name"], 100)
    customer_phone = _sanitize_phone(data.get("customer_phone", ""))
    customer_email = _sanitize_text(data.get("customer_email", ""), 100)
    notes = _sanitize_text(data.get("notes", ""), 500)

    # Validate name
    if len(customer_name) < 2:
        return jsonify({"success": False, "error": "Please enter your full name (at least 2 characters)"}), 400

    # Validate phone
    if len(customer_phone) < 7:
        return jsonify({"success": False, "error": "Please enter a valid phone number"}), 400

    # Validate email if provided
    if customer_email:
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
        if not email_pattern.match(customer_email):
            return jsonify({"success": False, "error": "Please enter a valid email address"}), 400

    # Validate date
    try:
        parsed_date = date.fromisoformat(booking_date)
        if parsed_date < date.today():
            return jsonify({"success": False, "error": "Booking date cannot be in the past"}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format"}), 400

    # Validate time format
    time_pattern = re.compile(r"^\d{2}:\d{2}$")
    if not time_pattern.match(start_time):
        return jsonify({"success": False, "error": "Invalid time format"}), 400

    with get_db() as session:
        # Verify service and staff exist
        service = session.query(Service).filter(Service.id == service_id, Service.is_active == True).first()
        if not service:
            return jsonify({"success": False, "error": "Selected service is not available"}), 400

        staff = session.query(Staff).filter(Staff.id == staff_id, Staff.is_active == True).first()
        if not staff:
            return jsonify({"success": False, "error": "Selected specialist is not available"}), 400

        # Resolve duration/price option (server-authoritative — never trust client price)
        custom_price = None
        end_time = None
        option_id = data.get("option_id")
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
                return jsonify({"success": False, "error": "Selected duration option is not available"}), 400
            custom_price = option.price
            end_time = minutes_to_time(time_to_minutes(start_time) + option.duration_minutes)

        # Find or create customer by phone (upsert logic)
        customer = session.query(Customer).filter(Customer.phone == customer_phone).first()
        if customer:
            # Update name/email if provided
            if customer_name and customer_name != customer.name:
                customer.name = customer_name
            if customer_email and not customer.email:
                customer.email = customer_email
        else:
            customer = Customer(
                name=customer_name,
                phone=customer_phone,
                email=customer_email if customer_email else None,
                notes=notes if notes else None,
                total_bookings=0,
            )
            session.add(customer)
            session.flush()

        # Create the appointment
        success, appointment, error_msg = BookingService.create_appointment(
            session=session,
            customer_id=customer.id,
            staff_id=staff_id,
            service_id=service_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            notes=notes if notes else None,
            custom_price=custom_price,
        )

        if not success:
            return jsonify({"success": False, "error": error_msg}), 409

        # Audit web booking
        AuditLogger.log(
            session,
            action="WEB_BOOKING",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            details=f"Web booking {appointment.appointment_number} by {customer_name} ({customer_phone})",
            source=f"Web/{request.remote_addr}",
        )

        ref = appointment.appointment_number

    logger.info(f"Web booking created: {ref}")
    return jsonify({
        "success": True,
        "booking_reference": ref,
        "redirect": f"/confirmation/{ref}",
        "message": f"Booking confirmed! Your reference is {ref}.",
    })

# ── SEO & Infrastructure Endpoints ─────────────────────────────────────────────

@public_bp.route("/robots.txt")
def robots_txt():
    """robots.txt for search engine crawlers."""
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /internal/\n"
        "Disallow: /api/\n"
        f"Sitemap: {request.url_root}sitemap.xml\n"
    )
    return body, 200, {"Content-Type": "text/plain; charset=utf-8"}


@public_bp.route("/sitemap.xml")
def sitemap_xml():
    """Dynamic sitemap listing public pages."""
    base = request.url_root.rstrip("/")
    pages = [
        ("/", "1.0", "daily"),
        ("/services", "0.9", "weekly"),
        ("/specialists", "0.8", "weekly"),
        ("/book", "0.9", "monthly"),
    ]
    urls = "".join(
        f"\n  <url>\n    <loc>{base}{path}</loc>\n"
        f"    <priority>{pri}</priority>\n    <changefreq>{freq}</changefreq>\n  </url>"
        for path, pri, freq in pages
    )
    body = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">{urls}\n</urlset>"
    return body, 200, {"Content-Type": "application/xml; charset=utf-8"}


@public_bp.route("/health")
def health():
    """Lightweight health-check for deployment platform monitoring."""
    try:
        from sqlalchemy import text
        with get_db() as session:
            session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "service": "bookease-web"}), 200
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        return jsonify({"status": "error", "service": "bookease-web"}), 503
