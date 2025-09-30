"""Database configuration and session management for development planning."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
)

AsyncSessionLocal = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:  # pragma: no cover - re-raise for caller handling
            await session.rollback()
            raise


async def init_database() -> None:
    """Ensure database schema exists."""
    from . import models  # noqa: F401  Import models for metadata registration

    async with _engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


async def shutdown_database() -> None:
    """Dispose of database engine resources."""
    await _engine.dispose()
