"""Web portal integration tests for BookEase.

Covers: public pages, SEO/infra endpoints, booking API flow, double-booking
prevention via the public API, server-side validation, internal staff auth &
RBAC, and rate limiting on the booking endpoint. Uses an isolated temp SQLite
database so the real data/bookease.db is never touched.
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
from web.app import create_app
from web.config import WebConfig
from web.rate_limit import booking_limiter


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def _isolated_db():
    """Swap the module-level engine/SessionLocal to a temp DB for the whole session."""
    tmpdir = tempfile.mkdtemp(prefix="bookease_test_")
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

    # Save originals and swap
    orig_engine = connection.engine
    orig_session = connection.SessionLocal
    orig_db_path = connection.DB_PATH
    connection.engine = test_engine
    connection.SessionLocal = test_session_local
    connection.DB_PATH = db_path

    # Create tables + seed
    Base.metadata.create_all(bind=test_engine)
    connection.init_db()

    yield

    # Restore
    connection.engine = orig_engine
    connection.SessionLocal = orig_session
    connection.DB_PATH = orig_db_path
    test_session_local.remove()
    test_engine.dispose()


@pytest.fixture(scope="session")
def _app(_isolated_db):
    """Build the Flask app once against the isolated DB."""
    app = create_app(WebConfig)
    app.testing = True
    return app


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear the booking rate limiter before every test so counts don't bleed."""
    booking_limiter._hits.clear()
    yield
    booking_limiter._hits.clear()


@pytest.fixture
def client(_app):
    """Fresh test client per test (cheap; shares the session-scoped app/DB)."""
    return _app.test_client()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _future_weekday(offset_days=4):
    """Return a YYYY-MM-DD string for a future Monday–Friday."""
    d = date.today() + timedelta(days=offset_days)
    while d.weekday() >= 5:  # skip Sat/Sun
        d += timedelta(days=1)
    return d.isoformat()


# ── Public Page Tests ──────────────────────────────────────────────────────────

def test_homepage_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Book" in r.data


def test_services_page_renders(client):
    r = client.get("/services")
    assert r.status_code == 200
    assert b"service" in r.data.lower() or b"Service" in r.data


def test_specialists_page_renders(client):
    r = client.get("/specialists")
    assert r.status_code == 200


def test_book_page_renders(client):
    r = client.get("/book")
    assert r.status_code == 200
    assert b"wizard" in r.data.lower() or b"Choose" in r.data


def test_book_page_with_preselect(client):
    r = client.get("/book?service_id=1&staff_id=1")
    assert r.status_code == 200


def test_404_page(client):
    r = client.get("/this-route-does-not-exist")
    assert r.status_code == 404


# ── SEO & Infra Endpoint Tests ─────────────────────────────────────────────────

def test_robots_txt(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert b"User-agent: *" in r.data
    assert b"Disallow: /internal/" in r.data
    assert b"Sitemap:" in r.data


def test_sitemap_xml(client):
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert "xml" in r.content_type
    assert b"<urlset" in r.data
    assert b"<loc>" in r.data


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


# ── Public API Tests ───────────────────────────────────────────────────────────

def test_api_services(client):
    r = client.get("/api/services")
    assert r.status_code == 200
    data = r.get_json()
    assert "services" in data
    assert isinstance(data["services"], list)
    assert len(data["services"]) > 0


def test_api_staff_filtered_by_service(client):
    r = client.get("/api/staff?service_id=1")
    assert r.status_code == 200
    staff = r.get_json()["staff"]
    assert isinstance(staff, list)


def test_api_slots_requires_params(client):
    r = client.get("/api/slots")
    assert r.status_code == 400


def test_api_slots_returns_list(client):
    future = _future_weekday(5)
    r = client.get(f"/api/slots?staff_id=1&service_id=1&date={future}")
    assert r.status_code == 200
    assert "slots" in r.get_json()


def test_api_slots_rejects_past_date(client):
    past = (date.today() - timedelta(days=1)).isoformat()
    r = client.get(f"/api/slots?staff_id=1&service_id=1&date={past}")
    assert r.status_code == 200
    assert r.get_json()["slots"] == []


# ── Booking Flow & Double-Booking Prevention ───────────────────────────────────

def _find_available_slot(client, staff_id, service_id, offset=6):
    """Scan upcoming weekdays for the first date with >=1 slot."""
    for i in range(offset, offset + 14):
        d = date.today() + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        iso = d.isoformat()
        r = client.get(f"/api/slots?staff_id={staff_id}&service_id={service_id}&date={iso}")
        slots = r.get_json().get("slots", [])
        if slots:
            return iso, slots[0]["start"]
    return None, None


def test_api_book_success(client):
    booking_date, start = _find_available_slot(client, staff_id=1, service_id=1, offset=6)
    assert booking_date, "No available slot found for booking test"
    payload = {
        "service_id": 1,
        "staff_id": 1,
        "date": booking_date,
        "start_time": start,
        "customer_name": "Test Customer",
        "customer_phone": "+15550001122",
        "customer_email": "test@example.com",
        "notes": "Web test booking",
    }
    r = client.post("/api/book", json=payload)
    data = r.get_json()
    assert r.status_code == 200
    assert data["success"] is True
    assert data["booking_reference"].startswith("BK-")
    assert data["redirect"].startswith("/confirmation/")


def test_api_book_double_booking_prevented(client):
    booking_date, start = _find_available_slot(client, staff_id=2, service_id=2, offset=20)
    assert booking_date, "No available slot found for double-booking test"
    payload = {
        "service_id": 2,
        "staff_id": 2,
        "date": booking_date,
        "start_time": start,
        "customer_name": "Conflict Customer A",
        "customer_phone": "+15550003344",
    }
    first = client.post("/api/book", json=payload)
    assert first.get_json()["success"] is True

    payload["customer_name"] = "Conflict Customer B"
    payload["customer_phone"] = "+15550005566"
    second = client.post("/api/book", json=payload)
    data = second.get_json()
    assert second.status_code == 409
    assert data["success"] is False


def test_api_book_missing_fields(client):
    r = client.post("/api/book", json={"service_id": 1})
    data = r.get_json()
    assert r.status_code == 400
    assert data["success"] is False
    assert "Missing" in data["error"]


def test_api_book_invalid_phone(client):
    r = client.post("/api/book", json={
        "service_id": 1, "staff_id": 1, "date": _future_weekday(8),
        "start_time": "10:00", "customer_name": "X", "customer_phone": "12",
    })
    data = r.get_json()
    assert r.status_code == 400
    assert data["success"] is False


def test_confirmation_page(client):
    booking_date, start = _find_available_slot(client, staff_id=3, service_id=3, offset=34)
    assert booking_date, "No available slot for confirmation test"
    book = client.post("/api/book", json={
        "service_id": 3, "staff_id": 3, "date": booking_date, "start_time": start,
        "customer_name": "Confirm Test", "customer_phone": "+15550007788",
    })
    ref = book.get_json()["booking_reference"]
    r = client.get(f"/confirmation/{ref}")
    assert r.status_code == 200
    assert ref.encode() in r.data


def test_confirmation_not_found(client):
    r = client.get("/confirmation/BK-NOPE-999")
    assert r.status_code == 404


# ── Internal Auth & RBAC Tests5  ────────────────────────────────────────────────

def test_internal_login_page_renders(client):
    r = client.get("/internal/login")
    assert r.status_code == 200
    assert b"Staff" in r.data or b"staff" in r.data


def test_internal_login_success(client):
    r = client.post("/internal/login", json={"username": "admin", "password": "admin123"})
    data = r.get_json()
    assert r.status_code == 200
    assert data["success"] is True
    assert data["role"] == "admin"


def test_internal_login_invalid_credentials(client):
    r = client.post("/internal/login", json={"username": "admin", "password": "wrong"})
    data = r.get_json()
    assert r.status_code == 401
    assert data["success"] is False


def test_internal_login_missing_fields(client):
    r = client.post("/internal/login", json={"username": ""})
    assert r.status_code == 400


def test_internal_dashboard_requires_auth(client):
    r = client.get("/internal/dashboard")
    assert r.status_code in (302, 303)
    assert "/internal/login" in r.headers.get("Location", "")


def test_internal_dashboard_after_login(client):
    with client.session_transaction() as sess:
        sess["internal_user_id"] = 1
        sess["internal_user_name"] = "System Administrator"
        sess["internal_user_role"] = "admin"
    r = client.get("/internal/dashboard")
    assert r.status_code == 200


# ── Rate Limiting ──────────────────────────────────────────────────────────────

def test_booking_rate_limit_enforced(client):
    """6 invalid booking requests within 60s → the 6th is rate-limited (429)."""
    last_status = None
    for _ in range(6):
        r = client.post("/api/book", json={"service_id": 1})
        last_status = r.status_code
        if r.status_code == 429:
            break
    assert last_status == 429

# ── Duration Options ───────────────────────────────────────────────────────────

def test_api_services_include_options(client):
    """Services with duration options expose them in the API."""
    r = client.get("/api/services")
    services = r.get_json()["services"]
    with_options = [s for s in services if s.get("options")]
    assert len(with_options) > 0
    # Deep Tissue Restoration Massage should have multiple options
    deep_tissue = next((s for s in services if "Deep Tissue" in s["name"]), None)
    assert deep_tissue is not None
    assert len(deep_tissue["options"]) >= 3
    opt = deep_tissue["options"][0]
    assert "id" in opt and "duration_minutes" in opt and "price" in opt


def test_api_slots_with_duration_override(client):
    """Slots endpoint accepts a duration override and returns valid slots."""
    future = _future_weekday(7)
    r = client.get(f"/api/slots?staff_id=3&service_id=3&date={future}&duration=30")
    assert r.status_code == 200
    slots = r.get_json()["slots"]
    # 30-min slots should be available on a working weekday
    assert isinstance(slots, list)
    if slots:
        assert "start" in slots[0] and "end" in slots[0]


def test_api_book_with_option_uses_option_price(client):
    """Booking with an option_id stores the option's price, not the service default."""
    # Fetch services to find an option
    services = client.get("/api/services").get_json()["services"]
    deep_tissue = next(s for s in services if "Deep Tissue" in s["name"])
    option = deep_tissue["options"][0]
    staff_id = deep_tissue["specialists"][0]["id"]

    booking_date, start = _find_available_slot(
        client, staff_id=staff_id, service_id=deep_tissue["id"], offset=40
    )
    if not booking_date:
        pytest.skip("No available slot for option-booking test")

    r = client.post("/api/book", json={
        "service_id": deep_tissue["id"],
        "staff_id": staff_id,
        "option_id": option["id"],
        "date": booking_date,
        "start_time": start,
        "customer_name": "Option Test Client",
        "customer_phone": "+15550009900",
    })
    data = r.get_json()
    assert r.status_code == 200
    assert data["success"] is True
    ref = data["booking_reference"]

    # Verify the stored price matches the option price
    conf = client.get(f"/confirmation/{ref}")
    assert conf.status_code == 200
    expected = f"${option['price']:.2f}"
    assert expected.encode() in conf.data


def test_api_book_invalid_option_rejected(client):
    """An option_id that doesn't belong to the service is rejected."""
    future = _future_weekday(9)
    r = client.post("/api/book", json={
        "service_id": 2,
        "staff_id": 2,
        "option_id": 999999,
        "date": future,
        "start_time": "10:00",
        "customer_name": "Bad Option Client",
        "customer_phone": "+15550001010",
    })
    data = r.get_json()
    assert r.status_code == 400
    assert data["success"] is False