"""Tests for booking creation, rescheduling, cancellation, and metrics."""

from datetime import date, timedelta
from src.core.booking_service import BookingService
from src.config import STATUS_CONFIRMED, STATUS_CANCELLED, STATUS_COMPLETED


def get_next_weekday(weekday_int: int) -> str:
    today = date.today()
    days_ahead = weekday_int - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).isoformat()


def test_create_appointment_success(db_session, sample_data):
    staff = sample_data["staff"]
    service = sample_data["service"]
    customer = sample_data["customer"]
    target_date = get_next_weekday(1)

    success, app, err = BookingService.create_appointment(
        session=db_session,
        customer_id=customer.id,
        staff_id=staff.id,
        service_id=service.id,
        booking_date=target_date,
        start_time="10:00",
        notes="First consultation",
    )

    assert success is True
    assert app is not None
    assert app.appointment_number.startswith(f"BK-{target_date.replace('-', '')}")
    assert app.start_time == "10:00"
    assert app.end_time == "11:00"
    assert app.price == 100.0
    assert app.status == STATUS_CONFIRMED
    assert err == ""


def test_double_booking_prevention(db_session, sample_data):
    staff = sample_data["staff"]
    service = sample_data["service"]
    customer = sample_data["customer"]
    target_date = get_next_weekday(1)

    # 1. First appointment 10:00 - 11:00
    ok1, app1, err1 = BookingService.create_appointment(
        session=db_session,
        customer_id=customer.id,
        staff_id=staff.id,
        service_id=service.id,
        booking_date=target_date,
        start_time="10:00",
    )
    assert ok1 is True

    # 2. Second appointment overlapping: 10:30 - 11:30
    ok2, app2, err2 = BookingService.create_appointment(
        session=db_session,
        customer_id=customer.id,
        staff_id=staff.id,
        service_id=service.id,
        booking_date=target_date,
        start_time="10:30",
    )
    assert ok2 is False
    assert app2 is None
    assert "already has an active appointment" in err2


def test_reschedule_appointment(db_session, sample_data):
    staff = sample_data["staff"]
    service = sample_data["service"]
    customer = sample_data["customer"]
    target_date = get_next_weekday(1)

    ok, app, _ = BookingService.create_appointment(
        session=db_session,
        customer_id=customer.id,
        staff_id=staff.id,
        service_id=service.id,
        booking_date=target_date,
        start_time="10:00",
    )
    assert ok is True

    # Reschedule to 15:00
    resched_ok, resched_app, err = BookingService.reschedule_appointment(
        session=db_session,
        appointment_id=app.id,
        new_date=target_date,
        new_start_time="15:00",
        reason="Client had schedule change",
    )
    assert resched_ok is True
    assert resched_app.start_time == "15:00"
    assert resched_app.end_time == "16:00"


def test_cancel_frees_slot_for_rebooking(db_session, sample_data):
    staff = sample_data["staff"]
    service = sample_data["service"]
    customer = sample_data["customer"]
    target_date = get_next_weekday(2)

    # Book slot 11:00 - 12:00
    ok, app, _ = BookingService.create_appointment(
        session=db_session,
        customer_id=customer.id,
        staff_id=staff.id,
        service_id=service.id,
        booking_date=target_date,
        start_time="11:00",
    )
    assert ok is True

    # Cancel it
    cancel_ok, cancel_app, _ = BookingService.cancel_appointment(
        session=db_session,
        appointment_id=app.id,
        reason="Emergency cancellation",
    )
    assert cancel_ok is True
    assert cancel_app.status == STATUS_CANCELLED

    # Now another booking at 11:00 should succeed!
    ok2, app2, err2 = BookingService.create_appointment(
        session=db_session,
        customer_id=customer.id,
        staff_id=staff.id,
        service_id=service.id,
        booking_date=target_date,
        start_time="11:00",
    )
    assert ok2 is True
    assert app2 is not None


def test_dashboard_metrics(db_session, sample_data):
    metrics = BookingService.get_dashboard_metrics(db_session)
    assert "total_customers" in metrics
    assert "total_revenue" in metrics
    assert "completion_rate" in metrics
    assert "chart_days" in metrics
    assert len(metrics["chart_days"]) == 7
