"""Telegram update handler for the Render worker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4
import io
import logging

from src.bot.schemas import TelegramMessage, TelegramUpdate
from src.clients.telegram_client import TelegramClient
from src.config import AppConfig
from src.files.index import FileProcessor
from src.security.access_control import AccessController
from src.services.dadata_service import DaDataError, DaDataService
from src.services.risk_service import RiskAnalysisService
from src.services.scoring_service import RiskScoringService
from src.services.validators import validate_inn
from src.storage.memory_store import JsonMemoryStore
from src.templates.message_templates import ACCESS_DENIED_TEXT, HELP_TEXT, START_TEXT


@dataclass(frozen=True)
class CommandPayload:
    """Parsed command payload."""

    name: str
    argument_text: str
    output_format: Optional[str]


@dataclass(frozen=True)
class HandlerDependencies:
    """Dependencies for processing updates."""

    config: AppConfig
    logger: logging.Logger
    telegram: TelegramClient
    dadata: DaDataService
    scoring: RiskScoringService
    risk_analysis: RiskAnalysisService
    memory_store: JsonMemoryStore
    file_processor: FileProcessor
    access_controller: AccessController


async def process_update(
    update: TelegramUpdate,
    deps: HandlerDependencies,
    request_id: str,
) -> None:
    """Process a Telegram update."""

    message = update.message or update.edited_message
    if not message or not message.chat:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    correlation_id = request_id or str(uuid4())

    if user_id is None or not deps.access_controller.is_allowed(user_id):
        await deps.telegram.send_message(chat_id, ACCESS_DENIED_TEXT)
        deps.logger.warning(
            "telegram access denied",
            extra={"request_id": correlation_id, "chat_id": chat_id, "status_code": 403},
        )
        return

    command_payload = _parse_command(message)
    try:
        if message.document:
            await _handle_document(message, command_payload, deps, correlation_id)
            return
        if command_payload:
            await _handle_command(message, command_payload, deps, correlation_id)
            return
        if message.text:
            await deps.telegram.send_message(chat_id, HELP_TEXT)
    except Exception as exc:  # pylint: disable=broad-except
        deps.logger.exception(
            "telegram update processing failed",
            extra={
                "request_id": correlation_id,
                "chat_id": chat_id,
                "status_code": 500,
            },
        )
        await deps.telegram.send_message(
            chat_id,
            f"Произошла ошибка обработки запроса. Код: {correlation_id}",
        )


def _parse_command(message: TelegramMessage) -> Optional[CommandPayload]:
    text = message.text or message.caption
    if not text or not text.startswith("/"):
        return None

    tokens = text.strip().split()
    command = tokens[0][1:]
    command = command.split("@", maxsplit=1)[0].lower()

    output_format = None
    remaining_tokens: list[str] = []
    for token in tokens[1:]:
        if token in {"--docx", "--file"}:
            output_format = "docx"
            continue
        if token == "--md":
            output_format = "md"
            continue
        remaining_tokens.append(token)

    return CommandPayload(
        name=command,
        argument_text=" ".join(remaining_tokens),
        output_format=output_format,
    )


async def _handle_document(
    message: TelegramMessage,
    command_payload: Optional[CommandPayload],
    deps: HandlerDependencies,
    request_id: str,
) -> None:
    chat_id = message.chat.id
    document = message.document
    if not document:
        return

    file_size = document.file_size or 0
    max_bytes = deps.config.max_file_size_mb * 1024 * 1024
    if file_size > max_bytes:
        await deps.telegram.send_message(
            chat_id, "Файл превышает лимит размера. Максимум 15 МБ."
        )
        return

    extension = _detect_extension(document.file_name, document.mime_type)
    if extension not in {".pdf", ".docx", ".txt"}:
        await deps.telegram.send_message(
            chat_id, "Неподдерживаемый формат. Разрешены PDF, DOCX, TXT."
        )
        return

    file_info = await deps.telegram.get_file(document.file_id)
    content = await deps.telegram.download_file(file_info.file_path)
    extracted_text = deps.file_processor.extract_text(io.BytesIO(content), ext=extension)

    deps.memory_store.update(
        chat_id,
        last_document_text=extracted_text,
        last_command="file_upload",
    )

    if command_payload and command_payload.name == "risks":
        await _send_risk_response(
            chat_id,
            extracted_text,
            command_payload.output_format,
            deps,
        )
        return

    await deps.telegram.send_message(
        chat_id, "Файл получен. Используйте команду /risks для анализа."
    )


async def _handle_command(
    message: TelegramMessage,
    command_payload: CommandPayload,
    deps: HandlerDependencies,
    request_id: str,
) -> None:
    chat_id = message.chat.id
    deps.memory_store.update(chat_id, last_command=command_payload.name)

    if command_payload.name in {"start"}:
        await deps.telegram.send_message(chat_id, START_TEXT)
        return
    if command_payload.name in {"help"}:
        await deps.telegram.send_message(chat_id, HELP_TEXT)
        return
    if command_payload.name == "ping":
        await deps.telegram.send_message(chat_id, "pong")
        return
    if command_payload.name == "clear_memory":
        deps.memory_store.clear_chat(chat_id)
        await deps.telegram.send_message(chat_id, "Память чата очищена.")
        return
    if command_payload.name == "new_task":
        deps.memory_store.clear_task(chat_id)
        await deps.telegram.send_message(chat_id, "Контекст задачи сброшен.")
        return
    if command_payload.name == "company_check":
        await _handle_company_check(command_payload, deps, chat_id, request_id)
        return
    if command_payload.name == "risks":
        await _handle_risks(message, command_payload, deps)
        return

    await deps.telegram.send_message(chat_id, HELP_TEXT)


async def _handle_company_check(
    command_payload: CommandPayload,
    deps: HandlerDependencies,
    chat_id: int,
    request_id: str,
) -> None:
    inn = command_payload.argument_text.strip()
    if not validate_inn(inn):
        await deps.telegram.send_message(chat_id, "Укажите корректный ИНН (10 или 12 цифр).")
        return

    try:
        company = await deps.dadata.find_company_by_inn(inn)
    except DaDataError as exc:
        deps.logger.error(
            "dadata request failed",
            extra={"request_id": request_id, "chat_id": chat_id, "status_code": 502},
        )
        await deps.telegram.send_message(chat_id, f"Ошибка DaData: {exc}")
        return

    if not company:
        await deps.telegram.send_message(chat_id, "Компания не найдена.")
        return

    assessment = deps.scoring.evaluate(company)
    response_lines = [
        "Карточка контрагента:",
        f"Название: {company.name}",
        f"ИНН: {company.inn}",
        f"ОГРН: {company.ogrn or 'нет данных'}",
        f"КПП: {company.kpp or 'нет данных'}",
        f"Адрес: {company.address or 'нет данных'}",
        f"Руководитель: {company.director or 'нет данных'}",
        f"Статус: {company.status or 'нет данных'}",
    ]
    if company.registration_date:
        response_lines.append(
            f"Дата регистрации: {company.registration_date.date().isoformat()}"
        )

    response_lines.append("")
    response_lines.append(f"Риск-уровень: {assessment.level}")
    response_lines.append("Причины:")
    response_lines.extend([f"- {reason}" for reason in assessment.reasons])

    await deps.telegram.send_message(chat_id, "\n".join(response_lines))


async def _handle_risks(
    message: TelegramMessage,
    command_payload: CommandPayload,
    deps: HandlerDependencies,
) -> None:
    chat_id = message.chat.id
    text = command_payload.argument_text.strip()

    if not text and message.reply_to_message:
        text = message.reply_to_message.text or ""

    if not text:
        memory = deps.memory_store.get(chat_id)
        text = memory.last_document_text or ""

    if not text:
        await deps.telegram.send_message(
            chat_id, "Пришлите текст договора или файл, затем вызовите /risks."
        )
        return

    await _send_risk_response(
        chat_id,
        text,
        command_payload.output_format,
        deps,
    )


async def _send_risk_response(
    chat_id: int,
    text: str,
    output_format: Optional[str],
    deps: HandlerDependencies,
) -> None:
    result = deps.risk_analysis.generate_risk_table(text)
    response = ["Таблица рисков:", result.markdown]

    if result.missing_data:
        response.append("")
        response.append(
            "ASSUMPTION: Недостаточно данных для полного анализа. "
            f"Отсутствуют разделы: {', '.join(result.missing_data)}."
        )

    message_text = "\n".join(response)
    await deps.telegram.send_message(chat_id, message_text)

    if output_format:
        filename, content = _build_risk_artifact(output_format, result.markdown)
        await deps.telegram.send_document(chat_id, filename, content, caption="Артефакт анализа")


def _build_risk_artifact(output_format: str, markdown: str) -> tuple[str, bytes]:
    if output_format == "md":
        return ("risk_table.md", markdown.encode("utf-8"))
    if output_format == "docx":
        from docx import Document

        document = Document()
        for line in markdown.splitlines():
            document.add_paragraph(line)
        buffer = io.BytesIO()
        document.save(buffer)
        return ("risk_table.docx", buffer.getvalue())
    return ("risk_table.txt", markdown.encode("utf-8"))


def _detect_extension(filename: Optional[str], mime_type: Optional[str]) -> str:
    if filename and "." in filename:
        return f".{filename.rsplit('.', maxsplit=1)[1].lower()}"
    if mime_type == "application/pdf":
        return ".pdf"
    if mime_type in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }:
        return ".docx"
    if mime_type in {"text/plain", "text/markdown"}:
        return ".txt"
    return ""
