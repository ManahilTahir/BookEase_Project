"""Tests for the Streamlit data-access layer (streamlit_app.db).

These tests exercise the same business logic as the Flask web tests
(test_web.py) but call the streamlit_app.db functions directly instead
of going through HTTP.  They use an isolated temp SQLite DB so the real
data/bookease.db is never touched.

No Streamlit installation required — db.py has zero Streamlit imports.
"""

import sys
import tempfile
from pathlib import Path
from datetime import date, timedelta

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session

import src.database.connection as connection
from src.database.models import Base


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def _isolated_db():
    tmpdir = tempfile.mkdtemp(prefix="bookease_st_test_")
    db_path = Path(tmpdir) / "test.db"
    db_url = f"sqlite:///{db_path.as_posix()}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)

    @event.listens_for(test_engine, "connect")
    def _pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    test_session_local = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=test_engine, expire_on_commit=False)
    )

    orig_engine = connection.engine
    orig_session = connection.SessionLocal
    orig_db_path = connection.DB_PATH
    connection.engine = test_engine
    connection.SessionLocal = test_session_local
    connection.DB_PATH = db_path

    Base.metadata.create_all(bind=test_engine)
    connection.init_db()

    yield

    connection.engine = orig_engine
    connection.SessionLocal = orig_session
    connection.DB_PATH = orig_db_path
    test_session_local.remove()
    test_engine.dispose()


@pytest.fixture(autouse=True)
def _use_isolated_db(_isolated_db):
    yield


# ── Helpers ────────────────────────────────────────────────────────────────────

def _future_weekday(offset_days=4):
    d = date.today() + timedelta(days=offset_days)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.isoformat()


def _find_slot(staff_id, service_id, offset=6, duration=None):
    from streamlit_app.db import get_available_slots
    for i in range(offset, offset + 14):
        d = date.today() + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        iso = d.isoformat()
        slots = get_available_slots(staff_id, service_id, iso, duration)
        if slots:
            return iso, slots[0]["start"]
    return None, None


# ── Settings & Home ────────────────────────────────────────────────────────────

def test_get_settings():
    from streamlit_app.db import get_settings
    s = get_settings()
    assert isinstance(s, dict)
    assert "business_name" in s
    assert "currency_symbol" in s


def test_get_home_data():
    from streamlit_app.db import get_home_data
    data = get_home_data()
    assert "categories" in data
    assert "staff_list" in data
    assert isinstance(data["categories"], dict)
    assert isinstance(data["staff_list"], list)
    assert len(data["staff_list"]) > 0


def test_home_categories_have_services():
    from streamlit_app.db import get_home_data
    data = get_home_data()
    total = sum(len(svcs) for svcs in data["categories"].values())
    assert total > 0


# ── Services ───────────────────────────────────────────────────────────────────

def test_get_services_with_specialists():
    from streamlit_app.db import get_services_with_specialists
    services = get_services_with_specialists()
    assert len(services) > 0
    svc = services[0]
    assert "id" in svc and "name" in svc and "price" in svc
    assert "specialists" in svc


def test_get_services_with_options():
    from streamlit_app.db import get_services_with_options
    services = get_services_with_options()
    assert len(services) > 0
    with_opts = [s for s in services if s.get("options")]
    assert len(with_opts) > 0
    deep_tissue = next((s for s in services if "Deep Tissue" in s["name"]), None)
    assert deep_tissue is not None
    assert len(deep_tissue["options"]) >= 3
    opt = deep_tissue["options"][0]
    assert "id" in opt and "duration_minutes" in opt and "price" in opt


# ── Specialists ────────────────────────────────────────────────────────────────

def test_get_specialists_with_services():
    from streamlit_app.db import get_specialists_with_services
    staff = get_specialists_with_services()
    assert len(staff) > 0
    s = staff[0]
    assert "id" in s and "name" in s and "role_title" in s
    assert "services" in s


def test_get_staff_for_service():
    from streamlit_app.db import get_staff_for_service
    staff = get_staff_for_service(1)
    assert isinstance(staff, list)


# ── Availability ───────────────────────────────────────────────────────────────

def test_get_available_slots_returns_list():
    from streamlit_app.db import get_available_slots
    future = _future_weekday(5)
    slots = get_available_slots(1, 1, future)
    assert isinstance(slots, list)


def test_get_available_slots_past_date_empty():
    from streamlit_app.db import get_available_slots
    past = (date.today() - timedelta(days=1)).isoformat()
    assert get_available_slots(1, 1, past) == []


def test_get_available_slots_invalid_date_empty():
    from streamlit_app.db import get_available_slots
    assert get_available_slots(1, 1, "not-a-date") == []


def test_get_available_slots_with_duration():
    from streamlit_app.db import get_available_slots
    future = _future_weekday(7)
    slots = get_available_slots(3, 3, future, duration=30)
    assert isinstance(slots, list)
    if slots:
        assert "start" in slots[0] and "end" in slots[0]


def test_get_available_dates():
    from streamlit_app.db import get_available_dates
    dates = get_available_dates(1, 1, days=14)
    assert isinstance(dates, list)


# ── Booking creation ───────────────────────────────────────────────────────────

def test_create_booking_success():
    from streamlit_app.db import create_booking
    booking_date, start = _find_slot(staff_id=1, service_id=1, offset=6)
    assert booking_date, "No available slot found"
    success, ref, error = create_booking({
        "service_id": 1,
        "staff_id": 1,
        "date": booking_date,
        "start_time": start,
        "customer_name": "Streamlit Test Customer",
        "customer_phone": "+15550001122",
        "customer_email": "sttest@example.com",
        "notes": "Streamlit test booking",
    })
    assert success is True
    assert ref.startswith("BK-")
    assert error == ""


def test_create_booking_double_booking_prevented():
    from streamlit_app.db import create_booking
    booking_date, start = _find_slot(staff_id=2, service_id=2, offset=20)
    assert booking_date, "No available slot found"
    payload = {
        "service_id": 2,
        "staff_id": 2,
        "date": booking_date,
        "start_time": start,
        "customer_name": "Conflict A",
        "customer_phone": "+15550003344",
    }
    success1, _, _ = create_booking(payload)
    assert success1 is True

    payload["customer_name"] = "Conflict B"
    payload["customer_phone"] = "+15550005566"
    success2, ref2, error2 = create_booking(payload)
    assert success2 is False
    assert ref2 is None
    assert error2 != ""


def test_create_booking_missing_fields():
    from streamlit_app.db import create_booking
    success, ref, error = create_booking({"service_id": 1})
    assert success is False
    assert "Missing" in error


def test_create_booking_invalid_phone():
    from streamlit_app.db import create_booking
    success, ref, error = create_booking({
        "service_id": 1, "staff_id": 1, "date": _future_weekday(8),
        "start_time": "10:00", "customer_name": "Valid Name", "customer_phone": "12",
    })
    assert success is False
    assert "phone" in error.lower()


def test_create_booking_invalid_name():
    from streamlit_app.db import create_booking
    success, ref, error = create_booking({
        "service_id": 1, "staff_id": 1, "date": _future_weekday(8),
        "start_time": "10:00", "customer_name": "A", "customer_phone": "+15550001234",
    })
    assert success is False
    assert "name" in error.lower()


def test_create_booking_past_date():
    from streamlit_app.db import create_booking
    past = (date.today() - timedelta(days=1)).isoformat()
    success, ref, error = create_booking({
        "service_id": 1, "staff_id": 1, "date": past,
        "start_time": "10:00", "customer_name": "Past Test", "customer_phone": "+15550009999",
    })
    assert success is False
    assert "past" in error.lower()


def test_create_booking_with_option_uses_option_price():
    from streamlit_app.db import create_booking, get_services_with_options, get_confirmation_data
    services = get_services_with_options()
    deep_tissue = next(s for s in services if "Deep Tissue" in s["name"])
    option = deep_tissue["options"][0]
    staff_id = deep_tissue["specialists"][0]["id"] if deep_tissue.get("specialists") else 3

    booking_date, start = _find_slot(staff_id=staff_id, service_id=deep_tissue["id"], offset=40)
    if not booking_date:
        pytest.skip("No available slot for option-booking test")

    success, ref, error = create_booking({
        "service_id": deep_tissue["id"],
        "staff_id": staff_id,
        "option_id": option["id"],
        "date": booking_date,
        "start_time": start,
        "customer_name": "Option Price Test",
        "customer_phone": "+15550008800",
    })
    assert success is True
    assert ref is not None

    appt = get_confirmation_data(ref)
    assert appt is not None
    assert abs(appt["price"] - option["price"]) < 0.01


def test_create_booking_invalid_option_rejected():
    from streamlit_app.db import create_booking
    future = _future_weekday(9)
    success, ref, error = create_booking({
        "service_id": 2,
        "staff_id": 2,
        "option_id": 999999,
        "date": future,
        "start_time": "10:00",
        "customer_name": "Bad Option Client",
        "customer_phone": "+15550001010",
    })
    assert success is False
    assert "option" in error.lower()


# ── Confirmation ───────────────────────────────────────────────────────────────

def test_get_confirmation_data_found():
    from streamlit_app.db import create_booking, get_confirmation_data
    booking_date, start = _find_slot(staff_id=3, service_id=3, offset=34)
    assert booking_date, "No available slot"
    success, ref, _ = create_booking({
        "service_id": 3, "staff_id": 3, "date": booking_date, "start_time": start,
        "customer_name": "Confirm Test", "customer_phone": "+15550007788",
    })
    assert success
    appt = get_confirmation_data(ref)
    assert appt is not None
    assert appt["appointment_number"] == ref
    assert "service_name" in appt
    assert "staff_name" in appt


def test_get_confirmation_data_not_found():
    from streamlit_app.db import get_confirmation_data
    assert get_confirmation_data("BK-NOPE-999") is None
    assert get_confirmation_data("") is None


# ── Internal auth ──────────────────────────────────────────────────────────────

def test_authenticate_success():
    from streamlit_app.db import authenticate_internal
    success, user, error = authenticate_internal("admin", "admin123")
    assert success is True
    assert user is not None
    assert user["role"] == "admin"
    assert user["username"] == "admin"
    assert error == ""


def test_authenticate_invalid_password():
    from streamlit_app.db import authenticate_internal
    success, user, error = authenticate_internal("admin", "wrong")
    assert success is False
    assert user is None
    assert "Invalid" in error


def test_authenticate_invalid_username():
    from streamlit_app.db import authenticate_internal
    success, user, error = authenticate_internal("nonexistent", "pass")
    assert success is False
    assert user is None


def test_authenticate_missing_fields():
    from streamlit_app.db import authenticate_internal
    success, user, error = authenticate_internal("", "")
    assert success is False
    assert "required" in error.lower()


def test_authenticate_owner_role():
    from streamlit_app.db import authenticate_internal
    success, user, _ = authenticate_internal("eleanor", "owner123")
    assert success is True
    assert user["role"] == "owner"


def test_authenticate_staff_role():
    from streamlit_app.db import authenticate_internal
    success, user, _ = authenticate_internal("marcus", "staff123")
    assert success is True
    assert user["role"] == "staff"


# ── Dashboard ──────────────────────────────────────────────────────────────────

def test_get_dashboard_summary():
    from streamlit_app.db import get_dashboard_summary
    m = get_dashboard_summary()
    assert isinstance(m, dict)
    assert "today_count" in m
    assert "total_revenue" in m
    assert "active_staff" in m
    assert "completion_rate" in m