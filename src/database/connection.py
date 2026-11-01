"""Database Connection & Session Management for BookEase."""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from src.config import DATABASE_URL, DB_PATH
from src.database.models import Base

# Create SQLite Engine with foreign keys enabled and WAL journal mode
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    future=True,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints, WAL mode, and busy timeout for SQLite concurrency.

    WAL mode allows concurrent readers alongside a single writer — essential
    when the desktop app and Streamlit web app share the same database file.
    ``busy_timeout`` makes SQLite wait (instead of immediately erroring with
    "database is locked") when both apps try to write at the same time.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


# Thread-safe Session Factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
)


@contextmanager
def get_db():
    """Context manager for safe database transactions.

    Calls ``SessionLocal.remove()`` on exit so the scoped-session registry
    is cleaned up per-thread — prevents stale sessions when Streamlit's
    thread pool reuses a thread for a different user/request.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        SessionLocal.remove()


def init_db():
    """Initialize database tables, run migrations, and seed initial data if needed."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    
    # Safe SQLite column migration for staff.specialties
    try:
        with engine.connect() as conn:
            cursor = conn.connection.cursor()
            cursor.execute("PRAGMA table_info(staff)")
            columns = [row[1] for row in cursor.fetchall()]
            if "specialties" not in columns:
                cursor.execute("ALTER TABLE staff ADD COLUMN specialties VARCHAR(255)")
                conn.connection.commit()
            cursor.close()
    except Exception:
        pass

    from src.database.seed_data import seed_initial_data, sync_and_seed_staff
    with get_db() as session:
        seed_initial_data(session)
        sync_and_seed_staff(session)
