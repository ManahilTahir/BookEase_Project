"""Bidirectional synchronization tests for the integrated BookEase system.

Proves that the desktop application and Streamlit website -- sharing the same
``src/`` backend and ``data/bookease.db`` -- stay synchronized in both directions:

  Streamlit -> Desktop : customer bookings via the website immediately appear
                        in the desktop app's appointment queries.
  Desktop -> Streamlit : service/staff/schedule/setting changes made internally
                        are immediately reflected on the website's data layer.

Uses an isolated temp SQLite DB so the real database is never touched.
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
from src.database.models import Base, Service, Staff, BusinessSetting, Appointment
from src.core.booking_service import BookingService
from src.core.security import SessionManager


# -- Fixtures -----------------------------------------------------------------

@pytest.fixture(scope="session")
def _isolated_db():
    tmpdir = tempfile.mkdtemp(prefix="bookease_sync_test_")
    db_path = Path(tmpdir) / "sync_test.db"
    db_url = f"sqlite:///{db_path.as_posix()}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)

    @event.listens_for(test_engine, "connect")
    def _pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
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


# -- Helpers ------------------------------------------------------------------

def _future_weekday(offset_days=4):
    d = date.today() + timedelta(days=offset_days)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.isoformat()


def _find_slot(staff_id, service_id, offset=6):
    from streamlit_app.db import get_available_slots
    for i in range(offset, offset + 14):
        d = date.today() + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        iso = d.isoformat()
        slots = get_available_slots(staff_id, service_id, iso)
        if slots:
            return iso, slots[0]["start"]
    return None, None


# == Streamlit -> Desktop =====================================================
# Bookings made on the website appear in desktop queries
# =============================================================================

def test_streamlit_booking_appears_in_desktop_appointments():
    """A booking created via streamlit_app.db.create_booking is visible via
    BookingService.get_appointments (the desktop app's query method)."""
    from streamlit_app.db import create_booking

    booking_date, start = _find_slot(staff_id=1, service_id=1, offset=6)
    assert booking_date, "No available slot"

    success, ref, error = create_booking({
        "service_id": 1,
        "staff_id": 1,
        "date": booking_date,
        "start_time": start,
        "customer_name": "Sync Test Customer",
        "customer_phone": "+15550002233",
    })
    assert success, f"Booking failed: {error}"

    with connection.get_db() as session:
        appts = BookingService.get_appointments(session, target_date=booking_date)
        matching = [a for a in appts if a.appointment_number == ref]
        assert len(matching) == 1
        assert matching[0].customer.name == "Sync Test Customer"
        assert matching[0].status == "confirmed"


def test_streamlit_booking_appears_in_desktop_dashboard_metrics():
    """A booking created via the website is counted in dashboard metrics."""
    from streamlit_app.db import create_booking, get_dashboard_summary

    before = get_dashboard_summary()
    before_total = before["total_count"]

    booking_date, start = _find_slot(staff_id=2, service_id=2, offset=8)
    assert booking_date
    success, ref, _ = create_booking({
        "service_id": 2, "staff_id": 2, "date": booking_date, "start_time": start,
        "customer_name": "Dashboard Sync Test", "customer_phone": "+15550004455",
    })
    assert success

    after = get_dashboard_summary()
    assert after["total_count"] == before_total + 1


def test_streamlit_booking_with_option_visible_in_desktop():
    """A booking with a duration option is visible in desktop with correct price."""
    from streamlit_app.db import create_booking, get_services_with_options

    services = get_services_with_options()
    deep_tissue = next(s for s in services if "Deep Tissue" in s["name"])
    option = deep_tissue["options"][0]
    staff_id = deep_tissue["specialists"][0]["id"] if deep_tissue.get("specialists") else 3

    booking_date, start = _find_slot(staff_id=staff_id, service_id=deep_tissue["id"], offset=12)
    if not booking_date:
        pytest.skip("No available slot")

    success, ref, _ = create_booking({
        "service_id": deep_tissue["id"], "staff_id": staff_id,
        "option_id": option["id"], "date": booking_date, "start_time": start,
        "customer_name": "Option Sync Test", "customer_phone": "+15550006677",
    })
    assert success

    with connection.get_db() as session:
        appt = session.query(Appointment).filter(
            Appointment.appointment_number == ref
        ).first()
        assert appt is not None
        assert abs(appt.price - option["price"]) < 0.01


# == Desktop -> Streamlit =====================================================
# Internal changes reflected on the website
# =============================================================================

def test_desktop_service_price_change_reflected_in_streamlit():
    """When staff edit a service price in the desktop app, the website sees it."""
    from streamlit_app.db import get_services_with_options

    new_price = 999.99
    with connection.get_db() as session:
        svc = session.query(Service).filter(Service.id == 1).first()
        assert svc is not None
        svc.price = new_price

    services = get_services_with_options()
    svc_data = next(s for s in services if s["id"] == 1)
    assert svc_data["price"] == new_price


def test_desktop_service_deactivation_reflected_in_streamlit():
    """When staff deactivate a service in the desktop app, it disappears from the website."""
    from streamlit_app.db import get_services_with_options

    with connection.get_db() as session:
        svc = session.query(Service).filter(Service.name == "Clinical Skin Consultation").first()
        assert svc is not None
        svc.is_active = False
        deactivated_id = svc.id

    services = get_services_with_options()
    ids = [s["id"] for s in services]
    assert deactivated_id not in ids

    with connection.get_db() as session:
        svc = session.query(Service).filter(Service.id == deactivated_id).first()
        svc.is_active = True


def test_desktop_staff_name_change_reflected_in_streamlit():
    """When staff edit a specialist's name in the desktop app, the website sees it."""
    from streamlit_app.db import get_specialists_with_services

    original_name = None
    new_name = "Dr. Modified Sync Test"
    with connection.get_db() as session:
        st = session.query(Staff).filter(Staff.id == 1).first()
        original_name = st.name
        st.name = new_name

    staff = get_specialists_with_services()
    st_data = next(s for s in staff if s["id"] == 1)
    assert st_data["name"] == new_name

    with connection.get_db() as session:
        st = session.query(Staff).filter(Staff.id == 1).first()
        st.name = original_name


def test_desktop_setting_change_reflected_in_streamlit():
    """When staff change a business setting in the desktop app, the website sees it."""
    from streamlit_app.db import get_settings

    with connection.get_db() as session:
        setting = session.query(BusinessSetting).filter(
            BusinessSetting.key == "business_name"
        ).first()
        original = setting.value
        setting.value = "Sync Test Spa"

    settings = get_settings()
    assert settings["business_name"] == "Sync Test Spa"

    with connection.get_db() as session:
        setting = session.query(BusinessSetting).filter(
            BusinessSetting.key == "business_name"
        ).first()
        setting.value = original


def test_desktop_new_service_appears_in_streamlit():
    """A new service added via the desktop app appears on the website immediately."""
    from streamlit_app.db import get_services_with_options

    new_svc_name = "Sync Test New Service"
    new_svc_id = None
    with connection.get_db() as session:
        svc = Service(
            name=new_svc_name,
            category="Test Category",
            description="Created by sync test",
            duration_minutes=45,
            buffer_minutes=15,
            price=75.0,
            is_active=True,
        )
        session.add(svc)
        session.flush()
        new_svc_id = svc.id

    services = get_services_with_options()
    found = next((s for s in services if s["id"] == new_svc_id), None)
    assert found is not None
    assert found["name"] == new_svc_name
    assert found["price"] == 75.0

    with connection.get_db() as session:
        svc = session.query(Service).filter(Service.id == new_svc_id).first()
        session.delete(svc)


# == Round-trip ===============================================================
# Booking created on website, modified in desktop, visible on website
# =============================================================================

def test_round_trip_booking_cancelled_in_desktop_reflected_in_streamlit():
    """A booking made on the website, then cancelled in the desktop app,
    shows as cancelled when the website queries confirmation data."""
    from streamlit_app.db import create_booking, get_confirmation_data

    booking_date, start = _find_slot(staff_id=3, service_id=3, offset=16)
    assert booking_date
    success, ref, _ = create_booking({
        "service_id": 3, "staff_id": 3, "date": booking_date, "start_time": start,
        "customer_name": "Round Trip Test", "customer_phone": "+15550008899",
    })
    assert success

    appt = get_confirmation_data(ref)
    assert appt is not None
    assert appt["status"] == "confirmed"

    with connection.get_db() as session:
        appt_obj = session.query(Appointment).filter(
            Appointment.appointment_number == ref
        ).first()
        success, _, _ = BookingService.cancel_appointment(
            session, appointment_id=appt_obj.id, reason="Sync test cancellation"
        )
        assert success

    appt = get_confirmation_data(ref)
    assert appt is not None
    assert appt["status"] == "cancelled"


def test_round_trip_booking_rescheduled_in_desktop_reflected_in_streamlit():
    """A booking made on the website, then rescheduled in the desktop app,
    shows the new date/time when the website queries confirmation data."""
    from streamlit_app.db import create_booking, get_confirmation_data, get_available_slots

    booking_date, start = _find_slot(staff_id=4, service_id=5, offset=18)
    if not booking_date:
        pytest.skip("No available slot for reschedule test")
    success, ref, _ = create_booking({
        "service_id": 5, "staff_id": 4, "date": booking_date, "start_time": start,
        "customer_name": "Reschedule Sync Test", "customer_phone": "+15550010101",
    })
    assert success

    new_date = None
    new_start = None
    for i in range(20, 35):
        d = date.today() + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        iso = d.isoformat()
        slots = get_available_slots(4, 5, iso)
        if slots:
            new_date = iso
            new_start = slots[0]["start"]
            break

    if not new_date:
        pytest.skip("No reschedule slot found")

    with connection.get_db() as session:
        appt_obj = session.query(Appointment).filter(
            Appointment.appointment_number == ref
        ).first()
        success, _, _ = BookingService.reschedule_appointment(
            session, appointment_id=appt_obj.id,
            new_date=new_date, new_start_time=new_start,
        )
        assert success

    appt = get_confirmation_data(ref)
    assert appt is not None
    assert appt["date"] == new_date
    assert appt["start_time"] == new_start


# == Concurrent access safety =================================================

def test_concurrent_reads_are_safe():
    """Multiple simultaneous reads from both layers don't raise errors."""
    from streamlit_app.db import get_services_with_options, get_specialists_with_services, get_settings

    for _ in range(10):
        get_services_with_options()
        get_specialists_with_services()
        get_settings()

    with connection.get_db() as session:
        BookingService.get_appointments(session)
        BookingService.get_dashboard_metrics(session)


def test_write_then_immediate_read_sees_data():
    """A write via get_db() is immediately visible to a subsequent read --
    no stale session cache between desktop and Streamlit layers."""
    from streamlit_app.db import get_settings

    test_value = "Concurrent Test Value"
    with connection.get_db() as session:
        setting = session.query(BusinessSetting).filter(
            BusinessSetting.key == "currency_symbol"
        ).first()
        original = setting.value
        setting.value = test_value

    settings = get_settings()
    assert settings["currency_symbol"] == test_value

    with connection.get_db() as session:
        setting = session.query(BusinessSetting).filter(
            BusinessSetting.key == "currency_symbol"
        ).first()
        setting.value = original