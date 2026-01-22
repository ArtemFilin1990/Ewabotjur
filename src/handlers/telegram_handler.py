"""Telegram update handler for Render worker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import io
import logging
import os

from src.bot.schemas import TelegramMessage, TelegramUpdate
from src.clients.telegram import TelegramClient
from src.config import AppConfig
from src.files.index import FileProcessor, DocumentGenerator
from src.services.dadata import DaDataClient
from src.services.risk_analysis import analyze_contract_risks, format_risk_table
from src.services.scoring import score_company, validate_inn
from src.storage.memory_store import ChatMemory, MemoryStore


@dataclass(frozen=True)
class CommandContext:
    """Parsed command context."""

    name: str
    args: str


HELP_TEXT = (
    "Доступные команды:\n"
    "/start — справка\n"
    "/help — список команд\n"
    "/ping — проверка доступности\n"
    "/company_check <ИНН> — проверка контрагента\n"
    "/risks — анализ рисков договора (можно приложить текст или файл)\n"
    "/clear_memory — очистить память чата\n"
    "/new_task — сбросить контекст задачи\n"
    "\n"
    "Для получения файла добавьте слово 'file' в команду /risks."
)


async def process_update(
    update: TelegramUpdate,
    config: AppConfig,
    logger: logging.Logger,
    request_id: str,
) -> None:
    """Process Telegram update and send responses."""

    message = _extract_message(update)
    if message is None or message.chat is None:
        logger.warning(
            "telegram update without message",
            extra={"request_id": request_id, "status_code": 200},
        )
        return

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    if config.enforce_telegram_whitelist:
        if not config.allowed_chat_ids or user_id not in config.allowed_chat_ids:
            await _safe_send_message(
                config, chat_id, "⛔ Доступ запрещён.", logger, request_id
            )
            logger.info(
                "telegram access denied",
                extra={
                    "request_id": request_id,
                    "telegram_user_id": user_id,
                    "status_code": 403,
                },
            )
            return

    telegram_client = TelegramClient(
        config.telegram_bot_token, config.http_timeout_seconds
    )
    memory_store = MemoryStore(config.memory_store_path)
    memory = memory_store.get(chat_id)

    command = _parse_command(message.text or "")
    if command:
        memory.last_command = command.name
        memory_store.update(chat_id, memory)
        await _handle_command(
            command,
            message,
            memory,
            config,
            telegram_client,
            memory_store,
            logger,
            request_id,
        )
        return

    if memory.last_command == "awaiting_risks_text" and message.text:
        await _handle_risks(
            message.text,
            chat_id,
            config,
            telegram_client,
            memory_store,
            logger,
            request_id,
            include_file=False,
        )
        memory.last_command = None
        memory_store.update(chat_id, memory)
        return

    if message.document:
        await _handle_document(
            message,
            config,
            telegram_client,
            memory_store,
            logger,
            request_id,
        )
        return

    if message.text:
        await _safe_send_message(
            config,
            chat_id,
            "Команда не распознана. Используйте /help.",
            logger,
            request_id,
        )


async def _handle_command(
    command: CommandContext,
    message: TelegramMessage,
    memory: ChatMemory,
    config: AppConfig,
    telegram_client: TelegramClient,
    memory_store: MemoryStore,
    logger: logging.Logger,
    request_id: str,
) -> None:
    chat_id = message.chat.id if message.chat else 0
    if command.name in {"start", "help"}:
        await _safe_send_message(config, chat_id, HELP_TEXT, logger, request_id)
        return

    if command.name == "ping":
        await _safe_send_message(config, chat_id, "pong", logger, request_id)
        return

    if command.name == "clear_memory":
        memory_store.clear(chat_id)
        await _safe_send_message(
            config, chat_id, "Память чата очищена.", logger, request_id
        )
        return

    if command.name == "new_task":
        memory_store.reset_task(chat_id)
        await _safe_send_message(
            config, chat_id, "Контекст задачи очищен.", logger, request_id
        )
        return

    if command.name == "company_check":
        await _handle_company_check(
            command.args,
            chat_id,
            config,
            telegram_client,
            logger,
            request_id,
        )
        return

    if command.name == "risks":
        include_file = "file" in command.args.lower()
        if message.document:
            extracted = await _extract_document_text(
                message,
                config,
                telegram_client,
                logger,
                request_id,
            )
            if extracted:
                await _handle_risks(
                    extracted,
                    chat_id,
                    config,
                    telegram_client,
                    memory_store,
                    logger,
                    request_id,
                    include_file=include_file,
                )
                return
        text_source = _extract_risk_text(message)
        if text_source:
            await _handle_risks(
                text_source,
                chat_id,
                config,
                telegram_client,
                memory_store,
                logger,
                request_id,
                include_file=include_file,
            )
            return
        if memory.last_document_text:
            await _handle_risks(
                memory.last_document_text,
                chat_id,
                config,
                telegram_client,
                memory_store,
                logger,
                request_id,
                include_file=include_file,
            )
            return
        memory.last_command = "awaiting_risks_text"
        memory_store.update(chat_id, memory)
        await _safe_send_message(
            config,
            chat_id,
            "Пришлите текст или файл договора для анализа рисков.",
            logger,
            request_id,
        )
        return

    await _safe_send_message(
        config,
        chat_id,
        "Команда не распознана. Используйте /help.",
        logger,
        request_id,
    )


async def _handle_company_check(
    inn: str,
    chat_id: int,
    config: AppConfig,
    telegram_client: TelegramClient,
    logger: logging.Logger,
    request_id: str,
) -> None:
    inn_value = inn.strip()
    if not validate_inn(inn_value):
        await _safe_send_message(
            config,
            chat_id,
            "ИНН должен состоять из 10 или 12 цифр.",
            logger,
            request_id,
        )
        return

    if not config.dadata_token:
        await _safe_send_message(
            config,
            chat_id,
            "DaData не настроена. Укажите DADATA_TOKEN.",
            logger,
            request_id,
        )
        return

    dadata_client = DaDataClient(
        config.dadata_token, config.dadata_secret, config.http_timeout_seconds
    )
    try:
        company = await dadata_client.find_by_inn(inn_value)
    except Exception:
        logger.exception(
            "dadata lookup failed",
            extra={"request_id": request_id, "status_code": 502},
        )
        await _safe_send_message(
            config,
            chat_id,
            _error_message(request_id),
            logger,
            request_id,
        )
        return

    if not company:
        await _safe_send_message(
            config,
            chat_id,
            "Компания не найдена по указанному ИНН.",
            logger,
            request_id,
        )
        return

    score = score_company(company)
    details = [
        f"Название: {company.name or '—'}",
        f"ИНН: {company.inn or '—'}",
        f"ОГРН: {company.ogrn or '—'}",
        f"КПП: {company.kpp or '—'}",
        f"Адрес: {company.address or '—'}",
        f"Руководитель: {company.director or '—'}",
        f"Статус: {company.status or '—'}",
        f"Дата регистрации: {company.registration_date or '—'}",
        f"Риск: {score.level}",
    ]
    if score.reasons:
        details.append("Причины: " + "; ".join(score.reasons))

    await _safe_send_message(
        config, chat_id, "\n".join(details), logger, request_id
    )


async def _handle_document(
    message: TelegramMessage,
    config: AppConfig,
    telegram_client: TelegramClient,
    memory_store: MemoryStore,
    logger: logging.Logger,
    request_id: str,
) -> None:
    if not message.document or not message.chat:
        return

    file_size = message.document.file_size or 0
    if file_size > config.max_file_size_mb * 1024 * 1024:
        await _safe_send_message(
            config,
            message.chat.id,
            f"Файл слишком большой. Максимум {config.max_file_size_mb} MB.",
            logger,
            request_id,
        )
        return

    filename = message.document.file_name or "document"
    extension = os.path.splitext(filename)[1].lower()
    if extension not in {".pdf", ".docx", ".txt"}:
        await _safe_send_message(
            config,
            message.chat.id,
            "Поддерживаются только PDF, DOCX и TXT файлы.",
            logger,
            request_id,
        )
        return

    try:
        file_info = await telegram_client.get_file(message.document.file_id)
        if not file_info.file_path:
            raise ValueError("file_path missing")
        content = await telegram_client.download_file(file_info.file_path)
        processor = FileProcessor()
        extracted_text = processor.extract_text(
            io.BytesIO(content), ext=extension
        ).strip()
    except Exception:
        logger.exception(
            "failed to process document",
            extra={"request_id": request_id, "status_code": 500},
        )
        await _safe_send_message(
            config,
            message.chat.id,
            _error_message(request_id),
            logger,
            request_id,
        )
        return

    if not extracted_text or extracted_text.startswith("[Ошибка"):
        await _safe_send_message(
            config,
            message.chat.id,
            "Не удалось извлечь текст из файла.",
            logger,
            request_id,
        )
        return

    memory = memory_store.get(message.chat.id)
    memory.last_document_text = extracted_text
    memory_store.update(message.chat.id, memory)
    await _safe_send_message(
        config,
        message.chat.id,
        "Файл обработан. Запустите /risks для анализа.",
        logger,
        request_id,
    )


async def _extract_document_text(
    message: TelegramMessage,
    config: AppConfig,
    telegram_client: TelegramClient,
    logger: logging.Logger,
    request_id: str,
) -> Optional[str]:
    if not message.document or not message.chat:
        return None

    file_size = message.document.file_size or 0
    if file_size > config.max_file_size_mb * 1024 * 1024:
        await _safe_send_message(
            config,
            message.chat.id,
            f"Файл слишком большой. Максимум {config.max_file_size_mb} MB.",
            logger,
            request_id,
        )
        return None

    filename = message.document.file_name or "document"
    extension = os.path.splitext(filename)[1].lower()
    if extension not in {".pdf", ".docx", ".txt"}:
        await _safe_send_message(
            config,
            message.chat.id,
            "Поддерживаются только PDF, DOCX и TXT файлы.",
            logger,
            request_id,
        )
        return None

    try:
        file_info = await telegram_client.get_file(message.document.file_id)
        if not file_info.file_path:
            raise ValueError("file_path missing")
        content = await telegram_client.download_file(file_info.file_path)
        processor = FileProcessor()
        extracted_text = processor.extract_text(
            io.BytesIO(content), ext=extension
        ).strip()
    except Exception:
        logger.exception(
            "failed to process document",
            extra={"request_id": request_id, "status_code": 500},
        )
        await _safe_send_message(
            config,
            message.chat.id,
            _error_message(request_id),
            logger,
            request_id,
        )
        return None

    if not extracted_text or extracted_text.startswith("[Ошибка"):
        await _safe_send_message(
            config,
            message.chat.id,
            "Не удалось извлечь текст из файла.",
            logger,
            request_id,
        )
        return None

    return extracted_text


async def _handle_risks(
    text: str,
    chat_id: int,
    config: AppConfig,
    telegram_client: TelegramClient,
    memory_store: MemoryStore,
    logger: logging.Logger,
    request_id: str,
    include_file: bool,
) -> None:
    result = analyze_contract_risks(text)
    table = format_risk_table(result)

    message_lines = ["Таблица рисков:", table]
    if result.missing_information:
        message_lines.append(
            "Недостаточно данных: " + ", ".join(result.missing_information)
        )
        message_lines.append(
            "ASSUMPTION: анализ выполнен по неполному тексту договора."
        )

    message_text = "\n".join(message_lines)
    await _safe_send_message(
        config, chat_id, message_text, logger, request_id
    )

    if include_file:
        try:
            generator = DocumentGenerator()
            content = generator.generate_docx(context={"content": message_text})
        except Exception:
            logger.exception(
                "failed to generate document",
                extra={"request_id": request_id, "status_code": 500},
            )
        else:
            await _safe_send_document(
                telegram_client,
                chat_id,
                "risk_table.docx",
                content,
                logger,
                request_id,
            )

    memory = memory_store.get(chat_id)
    memory.last_document_text = text
    memory.last_command = None
    memory_store.update(chat_id, memory)


def _parse_command(text: str) -> Optional[CommandContext]:
    if not text.startswith("/"):
        return None
    parts = text.split(maxsplit=1)
    command = parts[0][1:]
    command = command.split("@", maxsplit=1)[0]
    args = parts[1] if len(parts) > 1 else ""
    return CommandContext(name=command, args=args)


def _extract_message(update: TelegramUpdate) -> Optional[TelegramMessage]:
    if update.message:
        return update.message
    if update.edited_message:
        return update.edited_message
    if update.callback_query and update.callback_query.message:
        return update.callback_query.message
    return None


def _extract_risk_text(message: TelegramMessage) -> Optional[str]:
    if message.text:
        parts = message.text.split(maxsplit=1)
        if parts and parts[0].startswith("/risks"):
            return parts[1] if len(parts) > 1 else None
    if message.reply_to_message:
        if message.reply_to_message.text:
            return message.reply_to_message.text
    return None


async def _safe_send_message(
    config: AppConfig,
    chat_id: int,
    text: str,
    logger: logging.Logger,
    request_id: str,
) -> None:
    if not config.telegram_bot_token:
        logger.warning(
            "telegram token missing",
            extra={"request_id": request_id, "status_code": 500},
        )
        return
    client = TelegramClient(config.telegram_bot_token, config.http_timeout_seconds)
    await _safe_send_message_with_client(client, chat_id, text, logger, request_id)


async def _safe_send_message_with_client(
    client: TelegramClient,
    chat_id: int,
    text: str,
    logger: logging.Logger,
    request_id: str,
) -> None:
    try:
        await client.send_message(chat_id, text, parse_mode="Markdown")
    except Exception:
        logger.exception(
            "failed to send telegram message",
            extra={"request_id": request_id, "status_code": 502},
        )


async def _safe_send_document(
    client: TelegramClient,
    chat_id: int,
    filename: str,
    content: bytes,
    logger: logging.Logger,
    request_id: str,
) -> None:
    try:
        await client.send_document(chat_id, filename, content)
    except Exception:
        logger.exception(
            "failed to send telegram document",
            extra={"request_id": request_id, "status_code": 502},
        )


def _error_message(request_id: str) -> str:
    return f"Произошла ошибка. Код: {request_id}"
