"""Telegram update handling for the Render worker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import io
import uuid

from src.clients.telegram_api import TelegramApiError, TelegramClient
from src.files.index import FileProcessor
from src.logging_config import get_logger
from src.security.access_control import AccessController
from src.services.dadata import DadataClient, DadataError
from src.services.inn_validation import is_valid_inn
from src.services.risks import build_risk_table, render_risk_table
from src.services.scoring import score_company
from src.storage.memory_store import MemoryStore
from src.worker.config import WorkerConfig


logger = get_logger(__name__)


@dataclass(frozen=True)
class CommandContext:
    """Parsed command details."""

    command: str
    args: str
    wants_file: bool


def process_update(
    update: Dict[str, Any],
    config: WorkerConfig,
    memory_store: MemoryStore,
) -> None:
    """Process a single Telegram update payload."""

    message = _extract_message(update)
    if not message:
        return
    chat_id = _extract_chat_id(message)
    user_id = _extract_user_id(message)
    if chat_id is None:
        return

    access_controller = AccessController(",".join(str(x) for x in config.allowed_chat_ids))
    if not access_controller.is_allowed(chat_id):
        _safe_send_message(config, chat_id, "⛔ Доступ запрещён.")
        logger.warning(
            "chat access denied",
            extra={"telegram_user_id": user_id, "chat_id": chat_id},
        )
        return

    command = _parse_command(message)
    if not command:
        _handle_non_command(message, chat_id, config, memory_store)
        return

    if command.command in {"/start", "/help"}:
        _safe_send_message(config, chat_id, _help_text())
        memory_store.upsert(
            _update_memory(chat_id, memory_store, last_command=command.command)
        )
        return
    if command.command == "/ping":
        _safe_send_message(config, chat_id, "pong")
        memory_store.upsert(
            _update_memory(chat_id, memory_store, last_command=command.command)
        )
        return
    if command.command == "/clear_memory":
        memory_store.clear(chat_id)
        _safe_send_message(config, chat_id, "✅ Память очищена.")
        return
    if command.command == "/new_task":
        memory_store.reset_task(chat_id)
        _safe_send_message(config, chat_id, "✅ Контекст задачи сброшен.")
        return
    if command.command == "/company_check":
        _handle_company_check(command, chat_id, config)
        memory_store.upsert(
            _update_memory(chat_id, memory_store, last_command=command.command)
        )
        return
    if command.command == "/risks":
        _handle_risks(command, message, chat_id, config, memory_store)
        return

    _safe_send_message(config, chat_id, _help_text())


def _handle_non_command(
    message: Dict[str, Any],
    chat_id: int,
    config: WorkerConfig,
    memory_store: MemoryStore,
) -> None:
    document = message.get("document")
    if document:
        extracted = _extract_document_text(message, config)
        if extracted:
            memory_store.upsert(
                _update_memory(chat_id, memory_store, last_document_text=extracted)
            )
            _safe_send_message(
                config,
                chat_id,
                "✅ Файл получен. Отправьте команду /risks для анализа.",
            )
        return
    text = message.get("text")
    if text:
        _safe_send_message(config, chat_id, _help_text())


def _handle_company_check(command: CommandContext, chat_id: int, config: WorkerConfig) -> None:
    inn = command.args.strip()
    if not is_valid_inn(inn):
        _safe_send_message(config, chat_id, "❗ Укажите корректный ИНН (10 или 12 цифр).")
        return
    client = DadataClient(
        token=config.dadata_token,
        secret=config.dadata_secret,
        base_url=config.dadata_base_url,
        timeout_seconds=config.http_timeout_seconds,
    )
    try:
        profile = client.find_company_by_inn(inn)
    except DadataError as exc:
        request_id = _new_request_id()
        logger.exception(
            "dadata error",
            extra={"request_id": request_id, "chat_id": chat_id},
        )
        _safe_send_message(
            config,
            chat_id,
            f"⚠️ Не удалось получить данные DaData. Код: {request_id}",
        )
        return
    if not profile:
        _safe_send_message(config, chat_id, "ℹ️ Компания не найдена.")
        return
    score = score_company(profile)
    response = _format_company_response(profile, score)
    _safe_send_message(config, chat_id, response)


def _handle_risks(
    command: CommandContext,
    message: Dict[str, Any],
    chat_id: int,
    config: WorkerConfig,
    memory_store: MemoryStore,
) -> None:
    text = _extract_risks_text(command, message, config, memory_store)
    if not text:
        _safe_send_message(
            config,
            chat_id,
            "❗ Недостаточно данных. Отправьте текст договора или файл PDF/DOCX/TXT.",
        )
        return
    rows = build_risk_table(text)
    table = render_risk_table(rows)
    memory_store.upsert(
        _update_memory(chat_id, memory_store, last_document_text=text, last_command="/risks")
    )
    _safe_send_message(config, chat_id, table)
    if command.wants_file:
        filename = "risks_table.md"
        content = f"# Таблица рисков\n\n{table}\n".encode("utf-8")
        _safe_send_document(config, chat_id, filename, content)


def _extract_risks_text(
    command: CommandContext,
    message: Dict[str, Any],
    config: WorkerConfig,
    memory_store: MemoryStore,
) -> Optional[str]:
    if command.args:
        return command.args
    reply = message.get("reply_to_message") or {}
    reply_text = reply.get("text")
    if reply_text:
        return reply_text
    if message.get("document"):
        return _extract_document_text(message, config)
    memory = memory_store.get(_extract_chat_id(message) or 0)
    return memory.last_document_text


def _extract_document_text(message: Dict[str, Any], config: WorkerConfig) -> Optional[str]:
    document = message.get("document")
    if not document:
        return None
    chat_id = _extract_chat_id(message)
    if chat_id is None:
        return None
    file_size = document.get("file_size")
    if file_size and file_size > config.max_file_size_mb * 1024 * 1024:
        _safe_send_message(
            config,
            chat_id,
            f"❗ Файл превышает лимит {config.max_file_size_mb}MB.",
        )
        return None
    file_name = document.get("file_name", "")
    file_id = document.get("file_id")
    if not file_id:
        return None
    extension = f".{file_name.split('.')[-1].lower()}" if "." in file_name else ""
    if extension not in {".pdf", ".docx", ".txt"}:
        _safe_send_message(config, chat_id, "❗ Поддерживаются только PDF, DOCX или TXT.")
        return None
    telegram_client = _build_telegram_client(config)
    try:
        file_meta = telegram_client.get_file(file_id)
        if not file_meta.file_path:
            return None
        content = telegram_client.download_file(file_meta.file_path)
    except TelegramApiError as exc:
        request_id = _new_request_id()
        logger.exception(
            "telegram file download failed",
            extra={"request_id": request_id, "chat_id": chat_id},
        )
        _safe_send_message(
            config,
            chat_id,
            f"⚠️ Не удалось скачать файл. Код: {request_id}",
        )
        return None
    processor = FileProcessor(enable_ocr=config.enable_ocr)
    try:
        extracted = processor.extract_text(io.BytesIO(content), ext=extension)
    except ValueError as exc:
        _safe_send_message(config, chat_id, f"❗ Ошибка обработки файла: {exc}")
        return None
    if extracted.startswith("[Ошибка"):
        _safe_send_message(config, chat_id, "❗ Не удалось извлечь текст из файла.")
        return None
    return extracted


def _parse_command(message: Dict[str, Any]) -> Optional[CommandContext]:
    text = message.get("text") or message.get("caption")
    if not text or not text.startswith("/"):
        return None
    parts = text.split(maxsplit=1)
    command = parts[0].split("@")[0]
    args = parts[1] if len(parts) > 1 else ""
    wants_file = "--file" in args or "--doc" in args
    if wants_file:
        args = args.replace("--file", "").replace("--doc", "").strip()
    return CommandContext(command=command, args=args, wants_file=wants_file)


def _format_company_response(profile, score) -> str:
    lines = [
        "Контрагент (DaData)",
        f"- Название: {profile.name or 'TBD'}",
        f"- ИНН: {profile.inn or 'TBD'}",
        f"- ОГРН: {profile.ogrn or 'TBD'}",
        f"- КПП: {profile.kpp or 'TBD'}",
        f"- Адрес: {profile.address or 'TBD'}",
        f"- Руководитель: {profile.director or 'TBD'}",
        f"- Статус: {profile.status or 'TBD'}",
        f"- Дата регистрации: {profile.registration_date or 'TBD'}",
        "",
        f"Risk Score: {score.level}",
        "Причины:",
    ]
    lines.extend([f"- {reason}" for reason in score.reasons])
    return "\n".join(lines)


def _help_text() -> str:
    return (
        "Доступные команды:\n"
        "/ping — проверить связь\n"
        "/company_check <ИНН> — карточка компании + риск\n"
        "/risks [текст] [--file] — таблица рисков\n"
        "/clear_memory — очистить память\n"
        "/new_task — сбросить текущий контекст\n"
    )


def _extract_message(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return update.get("message") or update.get("edited_message")


def _extract_chat_id(message: Dict[str, Any]) -> Optional[int]:
    chat = message.get("chat") or {}
    return chat.get("id")


def _extract_user_id(message: Dict[str, Any]) -> Optional[int]:
    sender = message.get("from") or {}
    return sender.get("id")


def _update_memory(
    chat_id: int,
    memory_store: MemoryStore,
    last_document_text: Optional[str] = None,
    last_command: Optional[str] = None,
) -> Any:
    memory = memory_store.get(chat_id)
    if last_document_text is not None:
        memory.last_document_text = last_document_text
    if last_command is not None:
        memory.last_command = last_command
    return memory


def _safe_send_message(config: WorkerConfig, chat_id: int, text: str) -> None:
    telegram_client = _build_telegram_client(config)
    try:
        telegram_client.send_message(chat_id, text)
    except TelegramApiError:
        logger.exception("telegram send_message failed", extra={"chat_id": chat_id})


def _safe_send_document(
    config: WorkerConfig,
    chat_id: int,
    filename: str,
    content: bytes,
) -> None:
    telegram_client = _build_telegram_client(config)
    try:
        telegram_client.send_document(chat_id, filename, content)
    except TelegramApiError:
        logger.exception("telegram send_document failed", extra={"chat_id": chat_id})


def _build_telegram_client(config: WorkerConfig) -> TelegramClient:
    return TelegramClient(
        token=config.telegram_bot_token,
        base_url=config.telegram_api_base_url,
        timeout_seconds=config.http_timeout_seconds,
    )


def _new_request_id() -> str:
    return str(uuid.uuid4())
