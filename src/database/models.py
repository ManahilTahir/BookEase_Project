"""SQLAlchemy Database Models for BookEase."""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Association table between Staff and Service
staff_services = Table(
    "staff_services",
    Base.metadata,
    Column("staff_id", Integer, ForeignKey("staff.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", Integer, ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """User account model for authentication and role-based access."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="staff")  # admin, owner, staff
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    staff_profile = relationship("Staff", back_populates="user", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="user")
    created_appointments = relationship("Appointment", back_populates="created_by")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Staff(Base):
    """Staff member profile with working schedules and assigned services."""
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    role_title = Column(String(100), nullable=False, default="Specialist")
    specialties = Column(String(255), nullable=True)  # Key clinical/service specialties
    color_code = Column(String(20), nullable=False, default="#3B82F6")
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="staff_profile")
    services = relationship("Service", secondary=staff_services, back_populates="staff_members")
    schedules = relationship("StaffSchedule", back_populates="staff", cascade="all, delete-orphan")
    leaves = relationship("StaffLeave", back_populates="staff", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="staff")

    def __repr__(self):
        return f"<Staff {self.name} - {self.role_title} ({self.specialties})>"


class Service(Base):
    """Services offered by the business with duration and pricing."""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="General", index=True)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    buffer_minutes = Column(Integer, nullable=False, default=15)
    price = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    staff_members = relationship("Staff", secondary=staff_services, back_populates="services")
    appointments = relationship("Appointment", back_populates="service")
    options = relationship("ServiceOption", back_populates="service", cascade="all, delete-orphan", order_by="ServiceOption.sort_order")

    def __repr__(self):
        return f"<Service {self.name} (${self.price}, {self.duration_minutes}m)>"


class ServiceOption(Base):
    """Optional duration/price variants for a service.

    A service may offer multiple durations (e.g. 30/45/60 min) at different
    prices. If a service has no options, its default duration_minutes and
    price are used (backward compatible).
    """
    __tablename__ = "service_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(50), nullable=True)          # e.g. "30 min", "1 hour"
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    service = relationship("Service", back_populates="options")

    def __repr__(self):
        return f"<ServiceOption {self.label or f'{self.duration_minutes}m'} ${self.price}>"


class StaffSchedule(Base):
    """Weekly working schedule and lunch break for staff members."""
    __tablename__ = "staff_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    is_working = Column(Boolean, default=True, nullable=False)
    start_time = Column(String(5), nullable=False, default="09:00")  # HH:MM
    end_time = Column(String(5), nullable=False, default="18:00")    # HH:MM
    break_start = Column(String(5), nullable=False, default="13:00") # HH:MM
    break_end = Column(String(5), nullable=False, default="14:00")   # HH:MM

    staff = relationship("Staff", back_populates="schedules")

    __table_args__ = (
        UniqueConstraint("staff_id", "day_of_week", name="uq_staff_day"),
    )

    def __repr__(self):
        return f"<StaffSchedule Staff={self.staff_id} Day={self.day_of_week} ({self.start_time}-{self.end_time})>"


class StaffLeave(Base):
    """Staff vacations, sick leaves, and holidays."""
    __tablename__ = "staff_leaves"

    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False, index=True)    # YYYY-MM-DD
    reason = Column(String(255), nullable=True)
    status = Column(String(20), default="approved", nullable=False)  # approved, pending, rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    staff = relationship("Staff", back_populates="leaves")

    def __repr__(self):
        return f"<StaffLeave Staff={self.staff_id} {self.start_date} to {self.end_date}>"


class Customer(Base):
    """Customer profile and history."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), nullable=True, index=True)
    phone = Column(String(50), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    total_bookings = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    appointments = relationship("Appointment", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.name} ({self.phone})>"


class Appointment(Base):
    """Appointment bookings with timestamps, staff, service, and lifecycle status."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_number = Column(String(30), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)          # YYYY-MM-DD
    start_time = Column(String(5), nullable=False, index=True)     # HH:MM
    end_time = Column(String(5), nullable=False)                   # HH:MM
    status = Column(String(20), nullable=False, default="confirmed", index=True)
    price = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    reminder_sent = Column(Boolean, default=False, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="appointments")
    staff = relationship("Staff", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    created_by = relationship("User", back_populates="created_appointments")

    def __repr__(self):
        return f"<Appointment {self.appointment_number} on {self.date} {self.start_time}-{self.end_time} ({self.status})>"


class BusinessSetting(Base):
    """Key-value persistent business preferences and configurations."""
    __tablename__ = "business_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BusinessSetting {self.key}>"


class AuditLog(Base):
    """Audit trail logging all sensitive and administrative actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String(100), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_or_source = Column(String(50), default="Desktop Local", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_name} at {self.created_at}>"
