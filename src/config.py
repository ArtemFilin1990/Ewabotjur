"""Application configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional
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
    allowed_chat_ids: frozenset[int]
    worker_auth_token: str
    telegram_bot_token: str
    telegram_api_base: str
    dadata_token: Optional[str]
    dadata_secret: Optional[str]
    memory_store_path: str
    max_file_size_mb: int
    enable_ocr: bool


DEFAULT_HTTP_TIMEOUT_SECONDS = 15
DEFAULT_MAX_REQUEST_BODY_BYTES = 1024 * 1024
DEFAULT_REQUEST_ID_HEADER = "X-Request-Id"
DEFAULT_MAX_FILE_SIZE_MB = 15
DEFAULT_TELEGRAM_API_BASE = "https://api.telegram.org"
DEFAULT_MEMORY_STORE_PATH = "./data/memory_store.json"


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


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _parse_allowed_chat_ids() -> frozenset[int]:
    allowed_raw = os.getenv("ALLOWED_CHAT_IDS")
    if allowed_raw is None:
        allowed_raw = os.getenv("TELEGRAM_ALLOWED_IDS")
    return frozenset(_parse_int_list(allowed_raw))


def load_config() -> AppConfig:
    """Load application configuration from environment variables."""

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
        allowed_chat_ids=_parse_allowed_chat_ids(),
        worker_auth_token=_require_env("WORKER_AUTH_TOKEN"),
        telegram_bot_token=_require_env("TELEGRAM_BOT_TOKEN"),
        telegram_api_base=os.getenv("TELEGRAM_API_BASE", DEFAULT_TELEGRAM_API_BASE),
        dadata_token=os.getenv("DADATA_TOKEN"),
        dadata_secret=os.getenv("DADATA_SECRET"),
        memory_store_path=os.getenv("MEMORY_STORE_PATH", DEFAULT_MEMORY_STORE_PATH),
        max_file_size_mb=_parse_int(
            os.getenv("MAX_FILE_SIZE_MB"), DEFAULT_MAX_FILE_SIZE_MB
        ),
        enable_ocr=_parse_bool(os.getenv("ENABLE_OCR"), False),
    )
