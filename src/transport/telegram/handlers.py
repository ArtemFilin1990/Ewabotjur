"""Telegram webhook handlers and callback routing."""
from __future__ import annotations

import logging
from typing import Any

from src.config import settings
from src.db.engine import get_session_factory
from src.db.repositories import TelegramRepository, CompanyRepository
from src.services.formatter import format_affiliated, format_help, format_party_card, split_telegram_message
from src.services.report_service import ReportService
from src.transport.telegram.keyboards import main_menu
from src.utils.http import get_http_client
from src.utils.inn_parser import extract_inn, validate_inn

logger = logging.getLogger(__name__)


async def handle_update(update: dict[str, Any]) -> None:
    update_id = update.get("update_id")
    message = update.get("message") or {}
    callback = update.get("callback_query") or {}

    user_obj = (message.get("from") or callback.get("from") or {})
    chat_id = (message.get("chat") or {}).get("id") or (callback.get("message") or {}).get("chat", {}).get("id")
    if not chat_id:
        return

    async with get_session_factory()() as session:
        tg_repo = TelegramRepository(session)
        user = await tg_repo.upsert_user(
            tg_user_id=user_obj.get("id", chat_id),
            username=user_obj.get("username"),
            first_name=user_obj.get("first_name"),
            last_name=user_obj.get("last_name"),
        )

        if update_id is not None:
            is_new = await tg_repo.mark_update_processed(update_id=update_id, tg_user_id=user.tg_user_id)
            if not is_new:
                logger.info("Duplicate telegram update ignored", extra={"operation": "telegram.update", "result": "duplicate", "update_id": update_id})
                return

        if callback:
            await _handle_callback(chat_id, callback, user.last_inn)
            return

        text = (message.get("text") or "").strip()
        if text.startswith("/start"):
            await tg_repo.set_user_state(user, None)
            await send_message(chat_id, "👋 Добро пожаловать в Ewabotjur. Выберите действие:", reply_markup=main_menu())
            return

        if text.startswith("/help"):
            await send_message(chat_id, format_help(), reply_markup=main_menu())
            return

        if user.state == "awaiting_inn" or validate_inn(text) or extract_inn(text):
            inn = text if validate_inn(text) else extract_inn(text)
            if not inn or not validate_inn(inn):
                await send_message(chat_id, "❌ Введите корректный ИНН (10/12 цифр).")
                return

            await tg_repo.set_user_state(user, None)
            await tg_repo.set_last_inn(user, inn)
            await send_message(chat_id, f"✅ Принял ИНН {inn}. Готовлю отчёт…")

            report_service = ReportService(session)
            result = await report_service.get_or_build_report(tg_user_db_id=user.id, inn=inn, update_id=update_id)
            if not result:
                await send_message(chat_id, "❌ Компания по указанному ИНН не найдена.")
                return

            await send_message(chat_id, format_party_card(result.company_payload))
            await send_message(chat_id, f"⚠️ Риски\n{result.risk_summary}")
            await send_message(chat_id, format_affiliated(result.affiliated_payload))
            if result.ai_summary:
                await send_message(chat_id, f"🤖 AI-резюме (best effort)\n{result.ai_summary}")
            elif settings.openai_api_key:
                await send_message(chat_id, "Аналитика временно недоступна.")
            await send_message(chat_id, "Выберите следующее действие:", reply_markup=main_menu())
            return

        await send_message(chat_id, "Используйте меню ниже.", reply_markup=main_menu())


async def _handle_callback(chat_id: int, callback: dict[str, Any], last_inn: str | None) -> None:
    data = callback.get("data") or ""
    if data == "menu:check_inn":
        async with get_session_factory()() as session:
            user_repo = TelegramRepository(session)
            user = await user_repo.upsert_user(tg_user_id=callback.get("from", {}).get("id", chat_id), username=None, first_name=None, last_name=None)
            await user_repo.set_user_state(user, "awaiting_inn")
        await send_message(chat_id, "Отправьте ИНН (10/12 цифр).")
    elif data == "menu:help":
        await send_message(chat_id, format_help())
    elif data == "menu:contacts":
        await send_message(chat_id, "📞 Контакты: support@ewabotjur.local")
    elif data in {"menu:card", "menu:affiliated", "menu:risks"}:
        if not last_inn:
            await send_message(chat_id, "Сначала выполните проверку ИНН.")
            return
        async with get_session_factory()() as session:
            cache = await CompanyRepository(session).get_party_cache(last_inn)
        if not cache:
            await send_message(chat_id, "Кэш по последнему ИНН не найден, повторите проверку.")
            return
        if data == "menu:card":
            await send_message(chat_id, format_party_card(cache.payload))
        elif data == "menu:affiliated":
            await send_message(chat_id, format_affiliated(cache.affiliated_payload))
        else:
            await send_message(chat_id, "⚠️ Риски доступны после новой проверки ИНН (из истории запросов).")


async def send_message(chat_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    client = await get_http_client()
    for part in split_telegram_message(text):
        payload: dict[str, Any] = {"chat_id": chat_id, "text": part}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        response = await client.post(url, json=payload, timeout=settings.http_timeout_seconds)
        response.raise_for_status()
