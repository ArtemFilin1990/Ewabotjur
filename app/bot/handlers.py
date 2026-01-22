"""Telegram bot handlers."""

from __future__ import annotations

import asyncio
import hashlib
import uuid

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from app.config import AppConfig
from app.services.dadata import DadataError, fetch_company_profile
from app.services.risks import generate_risks_table
from app.services.scoring import score_company
from app.storage.memory import MemoryStore
from app.utils.files import extract_text_from_bytes
from app.utils.logging import get_logger
from app.bot.router import render_company_response


logger = get_logger(__name__)


def _is_allowed(chat_id: int, config: AppConfig) -> bool:
    return chat_id in config.allowed_chat_ids


def _log_context_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _error_response(correlation_id: str) -> str:
    return f"Ошибка выполнения запроса. Код: {correlation_id}"


def _validate_inn(inn: str) -> bool:
    return inn.isdigit() and len(inn) in (10, 12)


def setup_handlers(router: Router, config: AppConfig, memory: MemoryStore) -> None:
    """Register handlers on the router."""

    @router.message(Command("start"))
    async def start_command(message: Message) -> None:
        correlation_id = uuid.uuid4().hex
        if not _is_allowed(message.chat.id, config):
            await message.answer("Доступ запрещен.")
            return
        logger.info(
            "start command",
            extra={
                "chat_id": message.chat.id,
                "command": "/start",
                "correlation_id": correlation_id,
                "status": "ok",
            },
        )
        await message.answer(
            "Доступные команды:\n"
            "/ping — проверка связи\n"
            "/company_check <ИНН> — карточка контрагента\n"
            "/risks [текст] — таблица рисков\n"
            "/new_task — очистить контекст\n"
            "/clear_memory — удалить память"
        )

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        correlation_id = uuid.uuid4().hex
        if not _is_allowed(message.chat.id, config):
            await message.answer("Доступ запрещен.")
            return
        logger.info(
            "help command",
            extra={
                "chat_id": message.chat.id,
                "command": "/help",
                "correlation_id": correlation_id,
                "status": "ok",
            },
        )
        await message.answer(
            "Команды:\n"
            "/ping\n"
            "/company_check <ИНН>\n"
            "/risks [текст]\n"
            "/new_task\n"
            "/clear_memory"
        )

    @router.message(Command("ping"))
    async def ping_command(message: Message) -> None:
        correlation_id = uuid.uuid4().hex
        if not _is_allowed(message.chat.id, config):
            await message.answer("Доступ запрещен.")
            return
        logger.info(
            "ping command",
            extra={
                "chat_id": message.chat.id,
                "command": "/ping",
                "correlation_id": correlation_id,
                "status": "ok",
            },
        )
        await message.answer("pong")

    @router.message(Command("company_check"))
    async def company_check_command(message: Message, command: CommandObject) -> None:
        correlation_id = uuid.uuid4().hex
        if not _is_allowed(message.chat.id, config):
            await message.answer("Доступ запрещен.")
            return

        inn = (command.args or "").strip()
        if not inn:
            await message.answer("Укажите ИНН: /company_check <ИНН>")
            return
        if not _validate_inn(inn):
            await message.answer("ИНН должен содержать 10 или 12 цифр.")
            return

        try:
            profile = await fetch_company_profile(
                inn=inn,
                token=config.dadata_token,
                secret=config.dadata_secret,
                timeout_seconds=config.http_timeout_seconds,
            )
            score = score_company(profile)
            response_text = render_company_response(profile, score)
            await memory.set_last_context(message.chat.id, f"company_check:{inn}")
            logger.info(
                "company_check success",
                extra={
                    "chat_id": message.chat.id,
                    "command": "/company_check",
                    "correlation_id": correlation_id,
                    "status": "ok",
                },
            )
            await message.answer(response_text)
        except DadataError as exc:
            logger.error(
                "company_check failed",
                extra={
                    "chat_id": message.chat.id,
                    "command": "/company_check",
                    "correlation_id": correlation_id,
                    "status": "error",
                    "error_type": type(exc).__name__,
                },
            )
            await message.answer(_error_response(correlation_id))

    @router.message(Command("risks"))
    async def risks_command(message: Message, command: CommandObject) -> None:
        correlation_id = uuid.uuid4().hex
        if not _is_allowed(message.chat.id, config):
            await message.answer("Доступ запрещен.")
            return

        text = (command.args or "").strip()
        if not text:
            memory_state = await memory.get_memory(message.chat.id)
            text = memory_state.last_document_text or ""

        if not text:
            await message.answer("Нет текста для анализа. Пришлите документ или текст.")
            return

        try:
            table = generate_risks_table(text)
            await memory.set_last_context(message.chat.id, "risks")
            logger.info(
                "risks table generated",
                extra={
                    "chat_id": message.chat.id,
                    "command": "/risks",
                    "correlation_id": correlation_id,
                    "status": "ok",
                },
            )
            await message.answer(table)
        except Exception as exc:  # noqa: BLE001 - fallback logging
            logger.error(
                "risks command failed",
                extra={
                    "chat_id": message.chat.id,
                    "command": "/risks",
                    "correlation_id": correlation_id,
                    "status": "error",
                    "error_type": type(exc).__name__,
                },
            )
            await message.answer(_error_response(correlation_id))

    @router.message(Command("clear_memory"))
    async def clear_memory_command(message: Message) -> None:
        correlation_id = uuid.uuid4().hex
        if not _is_allowed(message.chat.id, config):
            await message.answer("Доступ запрещен.")
            return

        await memory.clear_memory(message.chat.id)
        logger.info(
            "clear_memory",
            extra={
                "chat_id": message.chat.id,
                "command": "/clear_memory",
                "correlation_id": correlation_id,
                "status": "ok",
            },
        )
        await message.answer("Память очищена.")

    @router.message(Command("new_task"))
    async def new_task_command(message: Message) -> None:
        correlation_id = uuid.uuid4().hex
        if not _is_allowed(message.chat.id, config):
            await message.answer("Доступ запрещен.")
            return

        await memory.clear_task_context(message.chat.id)
        logger.info(
            "new_task",
            extra={
                "chat_id": message.chat.id,
                "command": "/new_task",
                "correlation_id": correlation_id,
                "status": "ok",
            },
        )
        await message.answer("Контекст задачи очищен.")

    @router.message()
    async def document_handler(message: Message) -> None:
        if not message.document:
            return
        correlation_id = uuid.uuid4().hex
        if not _is_allowed(message.chat.id, config):
            await message.answer("Доступ запрещен.")
            return

        document = message.document
        if document.file_size and document.file_size > config.max_file_size_mb * 1024 * 1024:
            await message.answer("Файл слишком большой. Максимум 15 MB.")
            return

        try:
            file_info = await message.bot.get_file(document.file_id)
            file_bytes = await message.bot.download_file(file_info.file_path)
            content = file_bytes.read()
            extracted = await asyncio.to_thread(
                extract_text_from_bytes, document.file_name or "document", content
            )

            if not extracted.text:
                await message.answer("Не удалось извлечь текст из файла.")
                return

            await memory.set_last_document_text(message.chat.id, extracted.text)
            text_hash = _log_context_hash(extracted.text)
            logger.info(
                "document uploaded",
                extra={
                    "chat_id": message.chat.id,
                    "command": "document_upload",
                    "correlation_id": correlation_id,
                    "status": "ok",
                },
            )
            await message.answer(
                "Файл обработан. Текст сохранен для /risks."
                f"\nДлина: {len(extracted.text)} символов"
                f"\nХэш: {text_hash[:12]}"
            )
        except ValueError as exc:
            logger.warning(
                "unsupported file",
                extra={
                    "chat_id": message.chat.id,
                    "command": "document_upload",
                    "correlation_id": correlation_id,
                    "status": "unsupported",
                    "error_type": type(exc).__name__,
                },
            )
            await message.answer("Формат файла не поддерживается. Используйте PDF, DOCX, TXT.")
        except Exception as exc:  # noqa: BLE001 - fallback logging
            logger.error(
                "document processing failed",
                extra={
                    "chat_id": message.chat.id,
                    "command": "document_upload",
                    "correlation_id": correlation_id,
                    "status": "error",
                    "error_type": type(exc).__name__,
                },
            )
            await message.answer(_error_response(correlation_id))
