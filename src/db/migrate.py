"""Simple idempotent DB migrator.
Run: python -m src.db.migrate
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from src.db.engine import get_engine

logger = logging.getLogger(__name__)

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS tg_users (
        id SERIAL PRIMARY KEY,
        tg_user_id BIGINT UNIQUE NOT NULL,
        username VARCHAR(255),
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        state VARCHAR(64),
        last_inn VARCHAR(12),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS processed_updates (
        id SERIAL PRIMARY KEY,
        update_id BIGINT UNIQUE NOT NULL,
        tg_user_id BIGINT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS requests (
        id SERIAL PRIMARY KEY,
        tg_user_id INTEGER NOT NULL REFERENCES tg_users(id),
        inn VARCHAR(12) NOT NULL,
        ogrn VARCHAR(15),
        update_id BIGINT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS party_cache (
        id SERIAL PRIMARY KEY,
        inn VARCHAR(12) NOT NULL,
        ogrn VARCHAR(15),
        status VARCHAR(32),
        invalid BOOLEAN,
        management JSONB,
        founders JSONB,
        managers JSONB,
        finance JSONB,
        licenses JSONB,
        phones JSONB,
        emails JSONB,
        okveds JSONB,
        payload JSONB NOT NULL,
        affiliated_payload JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_party_cache_inn UNIQUE (inn)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS risk_assessments (
        id SERIAL PRIMARY KEY,
        request_id INTEGER NOT NULL REFERENCES requests(id),
        risk_score DOUBLE PRECISION NOT NULL,
        flags JSONB NOT NULL,
        summary TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_summaries (
        id SERIAL PRIMARY KEY,
        request_id INTEGER NOT NULL REFERENCES requests(id),
        summary TEXT NOT NULL,
        model VARCHAR(64) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_requests_created_at ON requests(created_at)",
    "CREATE INDEX IF NOT EXISTS ix_requests_user_id ON requests(tg_user_id)",
]


async def migrate() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            await conn.execute(text(stmt))
    logger.info("Database migration completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate())
