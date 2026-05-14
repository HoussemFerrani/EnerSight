"""
Supabase Postgres connection and session management.

Uses a single DATABASE_URL pointing at the Supabase pooler endpoint.
SQLAlchemy connects as the `postgres` user, which bypasses RLS — the backend
acts as a trusted gateway between Supabase Auth (frontend) and the database.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import get_settings

settings = get_settings()

DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a Postgres session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Schema is owned by Supabase migrations — this is a no-op kept for backwards
    compatibility with callers that expect it. To verify connectivity, use
    check_db_connection().
    """
    from backend.models import user, alert  # noqa: F401  (register ORM models)


def check_db_connection() -> bool:
    from sqlalchemy import text
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
