"""Tests for availability computation and collision detection."""

from datetime import date, timedelta
from src.core.availability import AvailabilityEngine, time_to_minutes
from src.database.models import StaffLeave, Appointment
from src.config import STATUS_CONFIRMED


def get_next_weekday(weekday_int: int) -> str:
    """Find date string for next occurrence of day of week (0=Mon, 6=Sun)."""
    today = date.today()
    days_ahead = weekday_int - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    target = today + timedelta(days=days_ahead)
    return target.isoformat()


def test_availability_normal_working_day(db_session, sample_data):
    staff = sample_data["staff"]
    service = sample_data["service"]

    # Next Tuesday (day 1)
    target_date = get_next_weekday(1)

    slots = AvailabilityEngine.get_available_slots(
        session=db_session,
        staff_id=staff.id,
        service_id=service.id,
        target_date=target_date,
        slot_interval=30,
    )

    assert len(slots) > 0
    
    # Ensure no slot intersects lunch break 13:00 to 14:00
    for slot in slots:
        s_min = time_to_minutes(slot["start"])
        e_min = time_to_minutes(slot["end"])
        # Lunch is 780 to 840
        assert not (max(s_min, 780) < min(e_min, 840)), f"Slot {slot} overlaps lunch break!"


def test_availability_non_working_day(db_session, sample_data):
    staff = sample_data["staff"]
    service = sample_data["service"]

    # Next Sunday (day 6)
    sunday_date = get_next_weekday(6)

    slots = AvailabilityEngine.get_available_slots(
        session=db_session,
        staff_id=staff.id,
        service_id=service.id,
        target_date=sunday_date,
    )

    assert len(slots) == 0


def test_availability_staff_on_leave(db_session, sample_data):
    staff = sample_data["staff"]
    service = sample_data["service"]

    target_date = get_next_weekday(2)  # Wednesday

    # Grant approved leave for that day
    leave = StaffLeave(
        staff_id=staff.id,
        start_date=target_date,
        end_date=target_date,
        reason="Doctor Appointment",
        status="approved",
    )
    db_session.add(leave)
    db_session.flush()

    assert AvailabilityEngine.is_staff_on_leave(db_session, staff.id, target_date) is True

    slots = AvailabilityEngine.get_available_slots(
        session=db_session,
        staff_id=staff.id,
        service_id=service.id,
        target_date=target_date,
    )
    assert len(slots) == 0


def test_slot_collision_validation(db_session, sample_data):
    staff = sample_data["staff"]
    target_date = get_next_weekday(3)  # Thursday

    # Test outside working hours
    valid, msg = AvailabilityEngine.validate_slot_availability(
        db_session, staff.id, target_date, "07:00", "08:00"
    )
    assert valid is False
    assert "outside working hours" in msg

    # Test lunch break conflict
    valid, msg = AvailabilityEngine.validate_slot_availability(
        db_session, staff.id, target_date, "13:30", "14:30"
    )
    assert valid is False
    assert "overlaps staff break" in msg

    # Test valid slot
    valid, msg = AvailabilityEngine.validate_slot_availability(
        db_session, staff.id, target_date, "10:00", "11:00"
    )
    assert valid is True
    assert msg == ""
