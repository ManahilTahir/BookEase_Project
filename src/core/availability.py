"""Availability Engine & Double-Booking Prevention Logic."""

from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from src.database.models import Staff, Service, StaffSchedule, StaffLeave, Appointment
from src.config import STATUS_CONFIRMED


def time_to_minutes(t_str: str) -> int:
    """Convert 'HH:MM' string to minutes from midnight."""
    h, m = map(int, t_str.split(":"))
    return h * 60 + m


def minutes_to_time(minutes: int) -> str:
    """Convert minutes from midnight to 'HH:MM' string."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


class AvailabilityEngine:
    """Engine for computing valid time slots and preventing booking collisions."""

    @staticmethod
    def is_staff_on_leave(session: Session, staff_id: int, target_date: str) -> bool:
        """Check if staff has approved leave on the target date (YYYY-MM-DD)."""
        leave = (
            session.query(StaffLeave)
            .filter(
                StaffLeave.staff_id == staff_id,
                StaffLeave.status == "approved",
                StaffLeave.start_date <= target_date,
                StaffLeave.end_date >= target_date,
            )
            .first()
        )
        return leave is not None

    @staticmethod
    def get_staff_daily_schedule(
        session: Session, staff_id: int, target_date: str
    ) -> Optional[StaffSchedule]:
        """Fetch working schedule for staff on the given date's day of week."""
        # Calculate day of week (0=Monday, 6=Sunday)
        dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        day_of_week = dt.weekday()

        return (
            session.query(StaffSchedule)
            .filter(
                StaffSchedule.staff_id == staff_id,
                StaffSchedule.day_of_week == day_of_week,
            )
            .first()
        )

    @staticmethod
    def get_booked_intervals(
        session: Session,
        staff_id: int,
        target_date: str,
        exclude_appointment_id: Optional[int] = None,
    ) -> List[Tuple[int, int]]:
        """Get all booked intervals [start_min, end_min] for staff on target_date."""
        query = session.query(Appointment).filter(
            Appointment.staff_id == staff_id,
            Appointment.date == target_date,
            Appointment.status.in_([STATUS_CONFIRMED]),
        )
        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)

        appointments = query.all()
        intervals = []
        for app in appointments:
            s_min = time_to_minutes(app.start_time)
            e_min = time_to_minutes(app.end_time)
            intervals.append((s_min, e_min))
        return intervals

    @classmethod
    def get_available_slots(
        cls,
        session: Session,
        staff_id: int,
        service_id: int,
        target_date: str,
        slot_interval: int = 15,
    ) -> List[Dict[str, str]]:
        """
        Compute all available time slots for a specific staff, service, and date.
        Returns list of dicts: [{'start': '09:00', 'end': '10:00'}, ...]
        """
        service = session.query(Service).filter(Service.id == service_id).first()
        if not service or not service.is_active:
            return []

        # 1. Check if staff is on leave
        if cls.is_staff_on_leave(session, staff_id, target_date):
            return []

        # 2. Get staff schedule for that day
        schedule = cls.get_staff_daily_schedule(session, staff_id, target_date)
        if not schedule or not schedule.is_working:
            return []

        work_start = time_to_minutes(schedule.start_time)
        work_end = time_to_minutes(schedule.end_time)
        break_start = time_to_minutes(schedule.break_start) if schedule.break_start else -1
        break_end = time_to_minutes(schedule.break_end) if schedule.break_end else -1

        duration = service.duration_minutes
        buffer = service.buffer_minutes

        # 3. Existing booked intervals
        booked_intervals = cls.get_booked_intervals(session, staff_id, target_date)

        available_slots = []
        current_start = work_start

        # Filter out past times if target_date is today
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_minutes = now.hour * 60 + now.minute if target_date == today_str else -1

        while current_start + duration <= work_end:
            slot_end = current_start + duration

            # Past time check
            if target_date == today_str and current_start <= current_time_minutes:
                current_start += slot_interval
                continue

            # Check collision with break time
            overlaps_break = False
            if break_start != -1 and break_end != -1:
                if max(current_start, break_start) < min(slot_end, break_end):
                    overlaps_break = True

            if overlaps_break:
                current_start += slot_interval
                continue

            # Check collision with existing appointments
            overlaps_booking = False
            for b_start, b_end in booked_intervals:
                # Slot overlaps existing appointment
                if max(current_start, b_start) < min(slot_end, b_end):
                    overlaps_booking = True
                    break

            if not overlaps_booking:
                available_slots.append({
                    "start": minutes_to_time(current_start),
                    "end": minutes_to_time(slot_end),
                    "duration": f"{duration} mins",
                })

            current_start += slot_interval

        return available_slots

    @classmethod
    def validate_slot_availability(
        cls,
        session: Session,
        staff_id: int,
        target_date: str,
        start_time: str,
        end_time: str,
        exclude_appointment_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Validate that a slot does not conflict with schedule, breaks, or existing bookings.
        Returns: (True, "") or (False, "Reason for conflict")
        """
        start_min = time_to_minutes(start_time)
        end_min = time_to_minutes(end_time)

        if start_min >= end_min:
            return False, "End time must be after start time."

        # Check Leave
        if cls.is_staff_on_leave(session, staff_id, target_date):
            return False, "Staff member is on approved leave on this date."

        # Check working schedule
        schedule = cls.get_staff_daily_schedule(session, staff_id, target_date)
        if not schedule or not schedule.is_working:
            return False, "Staff member is not scheduled to work on this day."

        work_start = time_to_minutes(schedule.start_time)
        work_end = time_to_minutes(schedule.end_time)

        if start_min < work_start or end_min > work_end:
            return (
                False,
                f"Requested slot ({start_time}-{end_time}) falls outside working hours ({schedule.start_time}-{schedule.end_time}).",
            )

        # Check break time
        if schedule.break_start and schedule.break_end:
            b_start = time_to_minutes(schedule.break_start)
            b_end = time_to_minutes(schedule.break_end)
            if max(start_min, b_start) < min(end_min, b_end):
                return (
                    False,
                    f"Requested slot overlaps staff break time ({schedule.break_start}-{schedule.break_end}).",
                )

        # Check overlapping appointments
        booked_intervals = cls.get_booked_intervals(
            session, staff_id, target_date, exclude_appointment_id
        )
        for b_start, b_end in booked_intervals:
            if max(start_min, b_start) < min(end_min, b_end):
                return (
                    False,
                    f"Staff already has an active appointment ({minutes_to_time(b_start)}-{minutes_to_time(b_end)}) during this time.",
                )

        return True, ""
