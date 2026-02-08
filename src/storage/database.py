"""Database connection helpers."""
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config import settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Create and cache async SQLAlchemy engine."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
    )
