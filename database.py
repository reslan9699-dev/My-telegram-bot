"""Async SQLAlchemy engine, session factory and declarative base.

The default backend is SQLite (aiosqlite). Swapping to PostgreSQL later only
requires changing DATABASE_URL (e.g. ``postgresql+asyncpg://...``); the rest of
the code is engine-agnostic.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings

logger = logging.getLogger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    """Declarative base for all ORM models."""


def _build_engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # Pool pre-ping keeps connections healthy for server-backed databases.
    return {"pool_pre_ping": True, "echo": False}


engine = create_async_engine(settings.database_url, **_build_engine_kwargs(settings.database_url))

if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        """SQLite does not enforce foreign keys by default; enable them."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI-style dependency: yields a session and closes it afterwards."""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables if they do not exist yet.

    This is a safety net; schema changes should be managed with Alembic
    migrations (``alembic upgrade head``).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized (tables ensured).")
