"""Webhook processing for Telegram updates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import logging

from src.bot.schemas import TelegramUpdate
from src.config import AppConfig


@dataclass(frozen=True)
class WebhookResult:
    """Result payload for webhook handling."""

    status_code: int
    payload: dict


def _extract_user_id(update: TelegramUpdate) -> Optional[int]:
    if update.callback_query:
        return update.callback_query.from_user.id
    if update.message and update.message.from_user:
        return update.message.from_user.id
    if update.edited_message and update.edited_message.from_user:
        return update.edited_message.from_user.id
    return None


def handle_update(
    update: TelegramUpdate,
    config: AppConfig,
    logger: logging.Logger,
    request_id: str,
) -> WebhookResult:
    """Validate and accept Telegram update payload."""

    user_id = _extract_user_id(update)
    if config.enforce_telegram_whitelist:
        if user_id is None or user_id not in config.allowed_telegram_ids:
            logger.warning(
                "telegram webhook rejected by whitelist",
                extra={
                    "request_id": request_id,
                    "telegram_user_id": user_id,
                    "status_code": 403,
                },
            )
            return WebhookResult(
                status_code=403,
                payload={"status": "forbidden", "request_id": request_id},
            )

    logger.info(
        "telegram webhook accepted",
        extra={
            "request_id": request_id,
            "telegram_user_id": user_id,
            "status_code": 200,
        },
    )
    return WebhookResult(
        status_code=200,
        payload={"status": "accepted", "request_id": request_id},
    )
