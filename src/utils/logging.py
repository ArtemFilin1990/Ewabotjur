"""
Утилиты для структурированного логирования.
"""
from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Optional


REQUEST_ID_CONTEXT: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def set_request_id(request_id: Optional[str]) -> Token:
    """Сохраняет request_id в контексте."""
    return REQUEST_ID_CONTEXT.set(request_id)


def reset_request_id(token: Token) -> None:
    """Сбрасывает request_id в контексте."""
    REQUEST_ID_CONTEXT.reset(token)


def _get_request_id() -> Optional[str]:
    return REQUEST_ID_CONTEXT.get()


class JsonLogFormatter(logging.Formatter):
    """JSON-формат логов с обязательными полями."""

    _RESERVED = frozenset({
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    })

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "operation": getattr(record, "operation", "-"),
            "result": getattr(record, "result", "-"),
            "duration_ms": getattr(record, "duration_ms", None),
            "request_id": getattr(record, "request_id", None) or _get_request_id(),
            "user_id": getattr(record, "user_id", None),
        }

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self._RESERVED and key not in payload
        }
        if extra_fields:
            payload["extra"] = extra_fields

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_level: str) -> None:
    """Настраивает root-логгер с JSON форматированием."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.addHandler(handler)
