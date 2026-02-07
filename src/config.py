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
    tg_webhook_secret: str
    worker_auth_token: str
    dadata_token: str
    dadata_secret: str | None
    openai_api_key: str
    openai_model: str
    openai_temperature: float
    openai_max_tokens: int
    bitrix_domain: str
    bitrix_client_id: str
    bitrix_client_secret: str
    bitrix_redirect_url: str
    max_file_size_mb: int
    memory_store_path: str
    use_mcp: bool
    mcp_server_url: str
    mcp_api_key: str


DEFAULT_HTTP_TIMEOUT_SECONDS = 15
DEFAULT_MAX_REQUEST_BODY_BYTES = 1024 * 1024
DEFAULT_REQUEST_ID_HEADER = "X-Request-Id"
DEFAULT_MAX_FILE_SIZE_MB = 15
DEFAULT_MEMORY_STORE_PATH = "./storage/memory.json"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_TEMPERATURE = 0.7
DEFAULT_OPENAI_MAX_TOKENS = 2000


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value)


def _parse_float(value: str | None, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value)


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
        tg_webhook_secret=os.getenv("TG_WEBHOOK_SECRET", ""),
        worker_auth_token=os.getenv("WORKER_AUTH_TOKEN", ""),
        dadata_token=os.getenv("DADATA_TOKEN", ""),
        dadata_secret=os.getenv("DADATA_SECRET"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        openai_temperature=_parse_float(
            os.getenv("OPENAI_TEMPERATURE"), DEFAULT_OPENAI_TEMPERATURE
        ),
        openai_max_tokens=_parse_int(
            os.getenv("OPENAI_MAX_TOKENS"), DEFAULT_OPENAI_MAX_TOKENS
        ),
        bitrix_domain=os.getenv("BITRIX_DOMAIN", ""),
        bitrix_client_id=os.getenv("BITRIX_CLIENT_ID", ""),
        bitrix_client_secret=os.getenv("BITRIX_CLIENT_SECRET", ""),
        bitrix_redirect_url=os.getenv("BITRIX_REDIRECT_URL", ""),
        max_file_size_mb=_parse_int(
            os.getenv("MAX_FILE_SIZE_MB"), DEFAULT_MAX_FILE_SIZE_MB
        ),
        memory_store_path=os.getenv("MEMORY_STORE_PATH", DEFAULT_MEMORY_STORE_PATH),
        use_mcp=_parse_bool(os.getenv("USE_MCP"), False),
        mcp_server_url=os.getenv("MCP_SERVER_URL", ""),
        mcp_api_key=os.getenv("MCP_API_KEY", ""),
    )
