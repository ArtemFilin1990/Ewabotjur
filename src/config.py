"""Application configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import os


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from environment variables."""

    app_name: str
    environment: str
    log_level: str
    http_timeout_seconds: int
    max_request_body_bytes: int
    request_id_header: str
    enforce_telegram_whitelist: bool
    allowed_chat_ids: frozenset[int]
    telegram_bot_token: str
    worker_auth_token: str
    dadata_token: str
    dadata_secret: str | None
    max_file_size_mb: int
    memory_store_path: str


DEFAULT_HTTP_TIMEOUT_SECONDS = 15
DEFAULT_MAX_REQUEST_BODY_BYTES = 1024 * 1024
DEFAULT_REQUEST_ID_HEADER = "X-Request-Id"
DEFAULT_MAX_FILE_SIZE_MB = 15
DEFAULT_MEMORY_STORE_PATH = "./storage/memory.json"


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value)


def _parse_int_list(value: str | None) -> Iterable[int]:
    if value is None or value.strip() == "":
        return []
    items = [item.strip() for item in value.split(",") if item.strip()]
    return [int(item) for item in items]


def load_config() -> AppConfig:
    """Load application configuration from environment variables."""

    allowed_ids = frozenset(_parse_int_list(os.getenv("ALLOWED_CHAT_IDS")))
    return AppConfig(
        app_name=os.getenv("APP_NAME", "jurist-bot"),
        environment=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        http_timeout_seconds=_parse_int(
            os.getenv("HTTP_TIMEOUT_SECONDS"), DEFAULT_HTTP_TIMEOUT_SECONDS
        ),
        max_request_body_bytes=_parse_int(
            os.getenv("MAX_REQUEST_BODY_BYTES"), DEFAULT_MAX_REQUEST_BODY_BYTES
        ),
        request_id_header=os.getenv("REQUEST_ID_HEADER", DEFAULT_REQUEST_ID_HEADER),
        enforce_telegram_whitelist=_parse_bool(
            os.getenv("ENFORCE_TELEGRAM_WHITELIST"), True
        ),
        allowed_chat_ids=allowed_ids,
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        worker_auth_token=os.getenv("WORKER_AUTH_TOKEN", ""),
        dadata_token=os.getenv("DADATA_TOKEN", ""),
        dadata_secret=os.getenv("DADATA_SECRET"),
        max_file_size_mb=_parse_int(
            os.getenv("MAX_FILE_SIZE_MB"), DEFAULT_MAX_FILE_SIZE_MB
        ),
        memory_store_path=os.getenv("MEMORY_STORE_PATH", DEFAULT_MEMORY_STORE_PATH),
    )
