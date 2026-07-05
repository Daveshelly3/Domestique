"""SQLAlchemy engine, session factory, and declarative base."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

# SQLite needs check_same_thread=False for FastAPI's threaded request handling.
connect_args = {"check_same_thread": False} if _is_sqlite else {}

# On serverless (Vercel), each function instance is short-lived and Postgres
# connections should not be held in a long-lived pool — use NullPool and let the
# Supabase transaction pooler (port 6543) manage real connections. pool_pre_ping
# guards against stale connections after a cold start.
engine_kwargs: dict = {"connect_args": connect_args, "future": True}
if not _is_sqlite:
    engine_kwargs.update(poolclass=NullPool, pool_pre_ping=True)

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session that is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Idempotent; fine for the single-user scaffold."""
    from . import models  # noqa: F401  (register models on Base.metadata)

    Base.metadata.create_all(bind=engine)
