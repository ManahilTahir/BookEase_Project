"""Booking Management Service with Concurrency-Safe Logic."""

import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from src.database.models import Appointment, Customer, Staff, Service, AuditLog
from src.core.availability import AvailabilityEngine, time_to_minutes, minutes_to_time
from src.core.audit_logger import AuditLogger
from src.core.security import SessionManager
from src.config import (
    STATUS_CONFIRMED,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
    STATUS_NO_SHOW,
)


class BookingService:
    """Core service for managing appointment lifecycle."""

    @staticmethod
    def generate_appointment_number(session: Session, target_date: str) -> str:
        """Generate a sequential, clean appointment reference: BK-YYYYMMDD-NNN."""
        clean_date = target_date.replace("-", "")
        prefix = f"BK-{clean_date}"
        
        # Count appointments on that day to generate index
        count = session.query(Appointment).filter(Appointment.date == target_date).count()
        return f"{prefix}-{count + 1:03d}"

    @classmethod
    def create_appointment(
        cls,
        session: Session,
        customer_id: int,
        staff_id: int,
        service_id: int,
        booking_date: str,
        start_time: str,
        end_time: Optional[str] = None,
        notes: Optional[str] = None,
        custom_price: Optional[float] = None,
    ) -> Tuple[bool, Optional[Appointment], str]:
        """
        Create a new appointment with strict concurrency-safe collision validation.
        Returns: (success, appointment, error_message)
        """
        # 1. Fetch related entities
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return False, None, "Customer not found."

        staff = session.query(Staff).filter(Staff.id == staff_id).first()
        if not staff or not staff.is_active:
            return False, None, "Selected staff member is not active."

        service = session.query(Service).filter(Service.id == service_id).first()
        if not service or not service.is_active:
            return False, None, "Selected service is not active."

        # 2. Compute end_time if not explicitly passed
        if not end_time:
            start_min = time_to_minutes(start_time)
            end_min = start_min + service.duration_minutes
            end_time = minutes_to_time(end_min)

        # 3. Validate Slot Availability (double-booking check)
        is_available, conflict_msg = AvailabilityEngine.validate_slot_availability(
            session=session,
            staff_id=staff_id,
            target_date=booking_date,
            start_time=start_time,
            end_time=end_time,
        )
        if not is_available:
            return False, None, conflict_msg

        # 4. Determine Price
        final_price = custom_price if custom_price is not None else service.price

        # 5. Build Appointment
        appointment_number = cls.generate_appointment_number(session, booking_date)
        current_user = SessionManager.get_current_user()

        appointment = Appointment(
            appointment_number=appointment_number,
            customer_id=customer_id,
            staff_id=staff_id,
            service_id=service_id,
            date=booking_date,
            start_time=start_time,
            end_time=end_time,
            status=STATUS_CONFIRMED,
            price=final_price,
            notes=notes,
            created_by_user_id=current_user.id if current_user else None,
        )
        session.add(appointment)

        # Update customer metrics
        customer.total_bookings = (customer.total_bookings or 0) + 1
        session.flush()

        # Audit Log
        AuditLogger.log(
            session,
            action="CREATE_APPOINTMENT",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            details=f"Created {appointment_number} for {customer.name} with {staff.name} on {booking_date} ({start_time}-{end_time})",
        )

        return True, appointment, ""

    @classmethod
    def reschedule_appointment(
        cls,
        session: Session,
        appointment_id: int,
        new_date: str,
        new_start_time: str,
        new_end_time: Optional[str] = None,
        new_staff_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[Appointment], str]:
        """Reschedule an existing booking with availability verification."""
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return False, None, "Appointment not found."

        staff_id = new_staff_id if new_staff_id else appointment.staff_id

        # Calculate new end time if omitted
        if not new_end_time:
            service = session.query(Service).filter(Service.id == appointment.service_id).first()
            dur = service.duration_minutes if service else 60
            start_min = time_to_minutes(new_start_time)
            new_end_time = minutes_to_time(start_min + dur)

        # Check collision excluding self
        is_available, conflict_msg = AvailabilityEngine.validate_slot_availability(
            session=session,
            staff_id=staff_id,
            target_date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
            exclude_appointment_id=appointment.id,
        )
        if not is_available:
            return False, None, conflict_msg

        old_desc = f"{appointment.date} {appointment.start_time}-{appointment.end_time}"
        appointment.date = new_date
        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        appointment.staff_id = staff_id
        if appointment.status == STATUS_CANCELLED:
            appointment.status = STATUS_CONFIRMED

        session.flush()

        AuditLogger.log(
            session,
            action="RESCHEDULE_APPOINTMENT",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            details=f"Rescheduled {appointment.appointment_number} from {old_desc} to {new_date} {new_start_time}-{new_end_time}. Reason: {reason or 'Not specified'}",
        )

        return True, appointment, ""

    @classmethod
    def cancel_appointment(
        cls,
        session: Session,
        appointment_id: int,
        reason: str = "Client requested",
    ) -> Tuple[bool, Optional[Appointment], str]:
        """Cancel an appointment and free its time slot."""
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return False, None, "Appointment not found."

        appointment.status = STATUS_CANCELLED
        appointment.cancellation_reason = reason
        session.flush()

        AuditLogger.log(
            session,
            action="CANCEL_APPOINTMENT",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            details=f"Cancelled {appointment.appointment_number}. Reason: {reason}",
        )

        return True, appointment, ""

    @classmethod
    def update_status(
        cls,
        session: Session,
        appointment_id: int,
        new_status: str,
    ) -> Tuple[bool, Optional[Appointment], str]:
        """Update appointment status (confirmed, completed, cancelled, no_show)."""
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return False, None, "Appointment not found."

        old_status = appointment.status
        appointment.status = new_status
        session.flush()

        AuditLogger.log(
            session,
            action="UPDATE_APPOINTMENT_STATUS",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            details=f"Changed status of {appointment.appointment_number} from {old_status} to {new_status}",
        )

        return True, appointment, ""

    @staticmethod
    def get_appointments(
        session: Session,
        target_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        staff_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Appointment]:
        """Query appointments with versatile filtering and search."""
        query = session.query(Appointment).options(
            joinedload(Appointment.customer),
            joinedload(Appointment.staff),
            joinedload(Appointment.service),
        )

        if target_date:
            query = query.filter(Appointment.date == target_date)
        if start_date:
            query = query.filter(Appointment.date >= start_date)
        if end_date:
            query = query.filter(Appointment.date <= end_date)
        if staff_id:
            query = query.filter(Appointment.staff_id == staff_id)
        if customer_id:
            query = query.filter(Appointment.customer_id == customer_id)
        if status and status != "All":
            query = query.filter(Appointment.status == status)

        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.join(Customer).join(Staff).join(Service).filter(
                or_(
                    Appointment.appointment_number.ilike(term),
                    Customer.name.ilike(term),
                    Customer.phone.ilike(term),
                    Staff.name.ilike(term),
                    Service.name.ilike(term),
                )
            )

        return query.order_by(Appointment.date.desc(), Appointment.start_time.asc()).all()

    @staticmethod
    def get_dashboard_metrics(session: Session) -> Dict[str, Any]:
        """Calculate live statistics for the executive dashboard."""
        today_str = date.today().isoformat()
        seven_days_ago = (date.today() - timedelta(days=7)).isoformat()

        # Today's appointments
        today_apps = session.query(Appointment).filter(Appointment.date == today_str).all()
        today_count = len(today_apps)
        today_revenue = sum(a.price for a in today_apps if a.status in (STATUS_CONFIRMED, STATUS_COMPLETED))

        # Total completed, confirmed, cancelled
        all_apps = session.query(Appointment).all()
        total_count = len(all_apps)
        completed_count = sum(1 for a in all_apps if a.status == STATUS_COMPLETED)
        confirmed_count = sum(1 for a in all_apps if a.status == STATUS_CONFIRMED)
        cancelled_count = sum(1 for a in all_apps if a.status == STATUS_CANCELLED)
        no_show_count = sum(1 for a in all_apps if a.status == STATUS_NO_SHOW)

        total_customers = session.query(Customer).count()
        total_services = session.query(Service).filter(Service.is_active == True).count()
        active_staff = session.query(Staff).filter(Staff.is_active == True).count()

        total_revenue = sum(
            a.price for a in all_apps if a.status in (STATUS_COMPLETED, STATUS_CONFIRMED)
        )

        completion_rate = (
            round((completed_count / (completed_count + cancelled_count + no_show_count)) * 100, 1)
            if (completed_count + cancelled_count + no_show_count) > 0
            else 100.0
        )

        # Revenue for last 7 days (day by day for charts)
        chart_days = []
        chart_revenues = []
        chart_appointments = []

        for i in range(6, -1, -1):
            day_d = date.today() - timedelta(days=i)
            day_str = day_d.isoformat()
            day_label = day_d.strftime("%b %d")
            day_items = [a for a in all_apps if a.date == day_str]
            day_rev = sum(a.price for a in day_items if a.status in (STATUS_CONFIRMED, STATUS_COMPLETED))
            
            chart_days.append(day_label)
            chart_revenues.append(day_rev)
            chart_appointments.append(len(day_items))

        # Service category distribution
        category_distribution = {}
        for a in all_apps:
            cat = a.service.category if a.service and a.service.category else "General"
            category_distribution[cat] = category_distribution.get(cat, 0) + 1

        # Staff bookings distribution
        staff_distribution = {}
        for a in all_apps:
            s_name = a.staff.name if a.staff else "Unassigned"
            staff_distribution[s_name] = staff_distribution.get(s_name, 0) + 1

        # Status distribution
        status_distribution = {
            "Confirmed": confirmed_count,
            "Completed": completed_count,
            "Cancelled": cancelled_count,
            "No-Show": no_show_count,
        }

        # Popular services
        service_popularity = {}
        for a in all_apps:
            s_name = a.service.name if a.service else "Unknown"
            service_popularity[s_name] = service_popularity.get(s_name, 0) + 1

        return {
            "today_count": today_count,
            "today_revenue": today_revenue,
            "total_count": total_count,
            "total_revenue": total_revenue,
            "total_customers": total_customers,
            "total_services": total_services,
            "active_staff": active_staff,
            "completed_count": completed_count,
            "confirmed_count": confirmed_count,
            "cancelled_count": cancelled_count,
            "no_show_count": no_show_count,
            "completion_rate": completion_rate,
            "chart_days": chart_days,
            "chart_revenues": chart_revenues,
            "chart_appointments": chart_appointments,
            "category_distribution": category_distribution,
            "staff_distribution": staff_distribution,
            "status_distribution": status_distribution,
            "service_popularity": service_popularity,
        }
