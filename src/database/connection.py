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
    """Enable foreign key constraints and WAL mode for SQLite concurrency."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
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
    """Context manager for safe database transactions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize database tables and seed initial data if needed."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    
    from src.database.seed_data import seed_initial_data
    with get_db() as session:
        seed_initial_data(session)
