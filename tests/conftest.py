import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import (
    Base,
    User,
    Staff,
    Service,
    StaffSchedule,
    StaffLeave,
    Customer,
    Appointment,
    BusinessSetting,
)
from src.core.security import hash_password, SessionManager
from src.config import ROLE_ADMIN, ROLE_OWNER, ROLE_STAFF


@pytest.fixture(scope="session")
def test_engine():
    """Create in-memory SQLite engine for fast testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provide a transactional database session rolled back after test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_data(db_session):
    """Seed test data for test cases."""
    admin = User(
        username="admin_test",
        email="admin@test.com",
        password_hash=hash_password("admin_pass"),
        full_name="Test Administrator",
        role=ROLE_ADMIN,
    )
    staff_user = User(
        username="staff_test",
        email="staff@test.com",
        password_hash=hash_password("staff_pass"),
        full_name="Dr. Alex Test",
        role=ROLE_STAFF,
    )
    db_session.add_all([admin, staff_user])
    db_session.flush()

    staff = Staff(
        user_id=staff_user.id,
        name="Dr. Alex Test",
        email="staff@test.com",
        phone="555-0101",
        role_title="Specialist",
        color_code="#3B82F6",
        is_active=True,
    )
    db_session.add(staff)
    db_session.flush()

    # Schedule: Mon-Fri 09:00 - 18:00, lunch 13:00 - 14:00
    for day in range(5):
        sched = StaffSchedule(
            staff_id=staff.id,
            day_of_week=day,
            is_working=True,
            start_time="09:00",
            end_time="18:00",
            break_start="13:00",
            break_end="14:00",
        )
        db_session.add(sched)

    # Weekend closed
    for day in [5, 6]:
        sched = StaffSchedule(
            staff_id=staff.id,
            day_of_week=day,
            is_working=False,
            start_time="09:00",
            end_time="18:00",
            break_start="13:00",
            break_end="14:00",
        )
        db_session.add(sched)

    service = Service(
        name="Comprehensive Exam",
        category="General",
        duration_minutes=60,
        buffer_minutes=15,
        price=100.0,
        is_active=True,
    )
    db_session.add(service)
    db_session.flush()
    staff.services.append(service)

    customer = Customer(
        name="Jane Doe",
        email="jane@example.com",
        phone="555-0202",
        notes="First time patient",
    )
    db_session.add(customer)
    db_session.flush()

    # Business Settings
    db_session.add(BusinessSetting(key="business_name", value="Test Practice Clinic"))
    db_session.add(BusinessSetting(key="currency_symbol", value="$"))
    db_session.flush()

    SessionManager.set_current_user(admin)

    return {
        "admin": admin,
        "staff_user": staff_user,
        "staff": staff,
        "service": service,
        "customer": customer,
    }
