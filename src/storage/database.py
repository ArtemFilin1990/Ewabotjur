"""Database connection helpers."""
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config import settings


def _ensure_async_driver(database_url: str) -> str:
    """Ensure the SQLAlchemy URL uses the asyncpg driver."""
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return database_url


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Create and cache async SQLAlchemy engine."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return create_async_engine(
        _ensure_async_driver(settings.database_url),
        pool_pre_ping=True,
    )
