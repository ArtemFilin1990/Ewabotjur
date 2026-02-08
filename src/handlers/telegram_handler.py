"""
Обработчик сообщений от Telegram
"""
import logging
from typing import Dict, Any, List
import httpx

from src.config import settings
from src.utils.inn_parser import extract_inn, validate_inn
from src.integrations.dadata import dadata_client
from src.integrations.openai_client import openai_client

logger = logging.getLogger(__name__)

# Глобальный клиент для переиспользования соединений
http_client = httpx.AsyncClient(timeout=30.0)


async def handle_telegram_update(update: Dict[str, Any]) -> None:
    """Обработка входящего update от Telegram"""
    message = update.get("message")
    
    if not message:
        return
    
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id:
        return

    # Ограничение длины входящего текста
    if len(text) > 1000:
        await send_telegram_message(
            chat_id,
            "❌ Сообщение слишком длинное. Пожалуйста, отправьте ИНН (10 или 12 цифр)."
        )
        return

    logger.info(
        "Processing Telegram message",
        extra={
            "operation": "telegram.message",
            "result": "received",
            "user_id": chat_id,
            "message_length": len(text),
        },
    )
    
    if text.startswith("/start"):
        await send_telegram_message(
            chat_id,
            "👋 Привет! Я бот для анализа контрагентов.\n\n"
            "Отправьте мне ИНН компании, и я предоставлю:\n"
            "✅ Данные из ЕГРЮЛ (через DaData)\n"
            "✅ Анализ рисков\n"
            "✅ Рекомендации по работе с контрагентом\n\n"
            "Просто пришлите ИНН (10 или 12 цифр)."
        )
        return
    
    if text.startswith("/help"):
        await send_telegram_message(
            chat_id,
            "📋 Как пользоваться:\n\n"
            "1. Отправьте ИНН компании (10 или 12 цифр)\n"
            "2. Бот найдет данные в DaData\n"
            "3. GPT проанализирует риски\n"
            "4. Вы получите рекомендации\n\n"
            "Пример: 7707083893"
        )
        return
    
    inn = extract_inn(text)
    
    if not inn:
        await send_telegram_message(
            chat_id,
            "❌ Не найден ИНН в вашем сообщении.\n"
            "Пожалуйста, отправьте ИНН (10 или 12 цифр).\n\n"
            "Пример: 7707083893"
        )
        return
    
    if not validate_inn(inn):
        await send_telegram_message(
            chat_id,
            f"❌ Некорректный ИНН: {inn}\n"
            "Проверьте правильность ввода."
        )
        return
    
    await send_telegram_message(
        chat_id,
        f"🔍 Ищу информацию по ИНН {inn}...\nПожалуйста, подождите."
    )
    
    try:
        company_data = await dadata_client.find_by_inn(inn)
        
        if not company_data:
            await send_telegram_message(
                chat_id,
                f"❌ Компания с ИНН {inn} не найдена в базе данных.\n"
                "Проверьте правильность ИНН."
            )
            return
        
        analysis = await openai_client.analyze_company(company_data)
        response = _format_response(company_data, analysis)
        
        await send_telegram_message(chat_id, response)
    
    except Exception as e:
        logger.error(
            "Error processing INN",
            extra={"operation": "telegram.inn", "result": "error", "inn": inn, "user_id": chat_id},
            exc_info=True,
        )
        await send_telegram_message(
            chat_id,
            f"❌ Произошла ошибка при обработке запроса:\n{str(e)}\n\n"
            "Пожалуйста, попробуйте позже."
        )


def _format_response(company_data: Dict[str, Any], analysis: str) -> str:
    parts = []
    parts.append("📊 **ИНФОРМАЦИЯ О КОМПАНИИ**\n")
    parts.append(f"**ИНН:** {company_data.get('inn', 'не указан')}")
    parts.append(f"**КПП:** {company_data.get('kpp', 'не указан')}")
    parts.append(f"**ОГРН:** {company_data.get('ogrn', 'не указан')}")
    
    if company_data.get("name"):
        parts.append(f"**Название:** {company_data['name'].get('short', 'не указано')}")
    
    if company_data.get("state"):
        parts.append(f"**Статус:** {company_data['state'].get('status', 'не указан')}")
    
    parts.append("\n" + "="*40 + "\n")
    parts.append(analysis)
    
    return "\n".join(parts)


def _smart_split_message(text: str, max_length: int = 4000) -> List[str]:
    """Разбивает сообщение, стараясь не разрывать строки."""
    if len(text) <= max_length:
        return [text]
        
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
            
        # Ищем ближайший перенос строки перед лимитом
        split_index = text.rfind('\n', 0, max_length)
        if split_index == -1:
            # Если нет переносов, ищем пробел
            split_index = text.rfind(' ', 0, max_length)
        
        if split_index == -1:
            # Если нет ни пробелов, ни переносов, режем жестко
            split_index = max_length
            
        parts.append(text[:split_index])
        text = text[split_index:].lstrip()
        
    return parts


async def send_telegram_message(chat_id: int, text: str) -> None:
    """Отправка сообщения в Telegram с поддержкой длинных текстов."""
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    parts = _smart_split_message(text)
    
    for part in parts:
        await _send_single_message(url, chat_id, part)


async def _send_single_message(url: str, chat_id: int, text: str) -> None:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        # Используем глобальный клиент
        response = await http_client.post(url, json=payload)
        response.raise_for_status()
        logger.info(
            "Message sent to Telegram chat",
            extra={"operation": "telegram.send", "result": "success", "user_id": chat_id},
        )
    except Exception:
        logger.error(
            "Error sending Telegram message",
            extra={"operation": "telegram.send", "result": "error", "user_id": chat_id},
            exc_info=True,
        )
        raise