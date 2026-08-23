"""Database session management, plus the snapshot-mode fallback.

PostgreSQL is a demo dependency, so it gets a fallback like everything else
in this project: if the database is unreachable, the backend serves enabled
content read-only from data/*.json (D021).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

log = logging.getLogger("psl.db")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass


class DatabaseState:
    """Tracks whether we are live on PostgreSQL or running on the snapshot."""

    def __init__(self) -> None:
        self.available: bool = False
        self.last_error: str | None = None

    def probe(self) -> bool:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.available = True
            self.last_error = None
        except Exception as exc:  # noqa: BLE001 - we genuinely want any failure here
            self.available = False
            self.last_error = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
            log.warning("PostgreSQL unavailable, snapshot mode active: %s", self.last_error)
        return self.available

    @property
    def mode(self) -> str:
        return "live" if self.available else "snapshot"


db_state = DatabaseState()


def get_db() -> Iterator[Session]:
    """FastAPI dependency for routes that require the live database."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db_optional() -> Iterator[Session | None]:
    """For read paths that can fall back to the snapshot."""
    if not db_state.available and not db_state.probe():
        yield None
        return
    session = SessionLocal()
    try:
        yield session
    except Exception:
        db_state.probe()
        raise
    finally:
        session.close()
