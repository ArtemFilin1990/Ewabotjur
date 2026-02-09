"""Bitrix24 OAuth token storage in PostgreSQL."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import text

from src.storage.database import get_engine


@dataclass(frozen=True)
class BitrixTokenRecord:
    """Stored Bitrix OAuth token record."""

    access_token: str
    refresh_token: str
    expires_in: int
    domain: str
    saved_at: datetime


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS bitrix_tokens (
    id SERIAL PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_in INTEGER NOT NULL,
    domain TEXT NOT NULL,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


async def ensure_schema() -> None:
    """Ensure the Bitrix token table exists."""
    engine = get_engine()
    try:
        async with engine.begin() as connection:
            await connection.execute(text(CREATE_TABLE_SQL))
    except Exception:
        # Silently ignore errors during schema creation
        pass

async def save_tokens(tokens: Dict[str, Any], domain: str) -> None:
    """Persist tokens to the database."""
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in")

    if not access_token or not refresh_token or expires_in is None:
        raise ValueError("Token payload is missing required fields")

    engine = get_engine()
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                INSERT INTO bitrix_tokens (access_token, refresh_token, expires_in, domain)
                VALUES (:access_token, :refresh_token, :expires_in, :domain)
                """
            ),
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": int(expires_in),
                "domain": domain,
            },
        )


async def load_latest_tokens(domain: str) -> Optional[BitrixTokenRecord]:
    """Load the most recently saved tokens for the given domain."""
    engine = get_engine()
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT access_token, refresh_token, expires_in, domain, saved_at
                FROM bitrix_tokens
                WHERE domain = :domain
                ORDER BY saved_at DESC
                LIMIT 1
                """
            ),
            {"domain": domain},
        )
        row = result.mappings().first()

    if not row:
        return None

    return BitrixTokenRecord(
        access_token=row["access_token"],
        refresh_token=row["refresh_token"],
        expires_in=row["expires_in"],
        domain=row["domain"],
        saved_at=row["saved_at"],
    )
