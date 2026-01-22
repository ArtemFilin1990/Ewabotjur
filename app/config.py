"""Application configuration and environment parsing."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import FrozenSet


@dataclass(frozen=True)
class AppConfig:
    """Typed configuration for the bot runtime."""

    bot_token: str
    allowed_chat_ids: FrozenSet[int]
    dadata_token: str
    dadata_secret: str | None
    log_level: str
    http_timeout_seconds: float
    max_file_size_mb: int
    memory_db_path: str


DEFAULT_HTTP_TIMEOUT_SECONDS = 15.0
DEFAULT_MAX_FILE_SIZE_MB = 15
DEFAULT_MEMORY_DB_PATH = "./data/memory.sqlite3"


def _parse_allowed_chat_ids(raw_value: str | None) -> FrozenSet[int]:
    if not raw_value:
        return frozenset()

    parsed_ids: list[int] = []
    for item in raw_value.split(","):
        item = item.strip()
        if not item:
            continue
        if not item.lstrip("-").isdigit():
            raise ValueError("ALLOWED_CHAT_IDS must be a comma-separated list of integers")
        parsed_ids.append(int(item))
    return frozenset(parsed_ids)


def load_config() -> AppConfig:
    """Load configuration from environment variables."""

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    dadata_token = os.getenv("DADATA_TOKEN")
    if not dadata_token:
        raise ValueError("DADATA_TOKEN is required")

    allowed_chat_ids = _parse_allowed_chat_ids(os.getenv("ALLOWED_CHAT_IDS"))

    dadata_secret = os.getenv("DADATA_SECRET")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    http_timeout_seconds = float(
        os.getenv("HTTP_TIMEOUT_SECONDS", str(DEFAULT_HTTP_TIMEOUT_SECONDS))
    )
    max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", str(DEFAULT_MAX_FILE_SIZE_MB)))
    memory_db_path = os.getenv("MEMORY_DB_PATH", DEFAULT_MEMORY_DB_PATH)

    return AppConfig(
        bot_token=bot_token,
        allowed_chat_ids=allowed_chat_ids,
        dadata_token=dadata_token,
        dadata_secret=dadata_secret,
        log_level=log_level,
        http_timeout_seconds=http_timeout_seconds,
        max_file_size_mb=max_file_size_mb,
        memory_db_path=memory_db_path,
    )
