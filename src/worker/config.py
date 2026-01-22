"""Configuration for the Render worker service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import os


DEFAULT_HTTP_TIMEOUT_SECONDS = 15
DEFAULT_MAX_FILE_SIZE_MB = 15
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_REQUEST_ID_HEADER = "X-Request-Id"
DEFAULT_TELEGRAM_API_BASE_URL = "https://api.telegram.org"
DEFAULT_DADATA_BASE_URL = "https://suggestions.dadata.ru"
DEFAULT_MEMORY_STORE_PATH = "./storage/memory_store.json"


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


@dataclass(frozen=True)
class WorkerConfig:
    """Runtime configuration for the worker service."""

    app_name: str
    environment: str
    log_level: str
    request_id_header: str
    http_timeout_seconds: int
    max_file_size_mb: int
    enable_ocr: bool
    allowed_chat_ids: frozenset[int]
    telegram_bot_token: str
    telegram_api_base_url: str
    worker_auth_token: str
    dadata_token: str
    dadata_secret: str | None
    dadata_base_url: str
    memory_store_path: str


def load_worker_config() -> WorkerConfig:
    """Load worker configuration from environment variables."""

    allowed_ids = frozenset(_parse_int_list(os.getenv("ALLOWED_CHAT_IDS")))
    dadata_secret = os.getenv("DADATA_SECRET")
    return WorkerConfig(
        app_name=os.getenv("APP_NAME", "jurist-worker"),
        environment=os.getenv("APP_ENV", "production"),
        log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL),
        request_id_header=os.getenv("REQUEST_ID_HEADER", DEFAULT_REQUEST_ID_HEADER),
        http_timeout_seconds=_parse_int(
            os.getenv("HTTP_TIMEOUT_SECONDS"), DEFAULT_HTTP_TIMEOUT_SECONDS
        ),
        max_file_size_mb=_parse_int(
            os.getenv("MAX_FILE_SIZE_MB"), DEFAULT_MAX_FILE_SIZE_MB
        ),
        enable_ocr=_parse_bool(os.getenv("ENABLE_OCR"), False),
        allowed_chat_ids=allowed_ids,
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_api_base_url=os.getenv(
            "TELEGRAM_API_BASE_URL", DEFAULT_TELEGRAM_API_BASE_URL
        ),
        worker_auth_token=os.getenv("WORKER_AUTH_TOKEN", ""),
        dadata_token=os.getenv("DADATA_TOKEN", ""),
        dadata_secret=dadata_secret if dadata_secret else None,
        dadata_base_url=os.getenv("DADATA_BASE_URL", DEFAULT_DADATA_BASE_URL),
        memory_store_path=os.getenv("MEMORY_STORE_PATH", DEFAULT_MEMORY_STORE_PATH),
    )
