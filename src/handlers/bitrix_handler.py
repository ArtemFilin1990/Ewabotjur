"""
Обработчик событий от Bitrix24
"""
import logging
from typing import Dict, Any

from src.utils.inn_parser import extract_inn, validate_inn
from src.integrations.dadata import dadata_client
from src.integrations.openai_client import openai_client
from src.integrations.bitrix24.api import bitrix_client

logger = logging.getLogger(__name__)


async def handle_bitrix_event(event: Dict[str, Any]) -> None:
    """
    Обработка события от Bitrix24 imbot
    
    Args:
        event: Данные события от Bitrix24
    """
    event_type = event.get("event")
    
    logger.info(
        "Processing Bitrix event",
        extra={"operation": "bitrix.event", "result": "received", "event": event_type},
    )
    
    # Обработка события нового сообщения
    if event_type == "ONIMBOTMESSAGEADD":
        await handle_message_add(event)
    else:
        logger.debug(
            "Unhandled event type",
            extra={"operation": "bitrix.event", "result": "ignored", "event": event_type},
        )


async def handle_message_add(event: Dict[str, Any]) -> None:
    """
    Обработка нового сообщения в чате Bitrix24
    
    Args:
        event: Данные события
    """
    # Извлечение данных сообщения
    data = event.get("data", {})
    message_text = data.get("PARAMS", {}).get("MESSAGE", "")
    dialog_id = data.get("PARAMS", {}).get("DIALOG_ID")
    user_id = data.get("USER", {}).get("ID")
    
    if not dialog_id:
        logger.warning(
            "No dialog_id in Bitrix event",
            extra={"operation": "bitrix.message", "result": "invalid"},
        )
        return
    
    # Проверка что это не сообщение от самого бота
    if data.get("PARAMS", {}).get("FROM_USER_ID") == data.get("BOT", {}).get("ID"):
        logger.debug(
            "Ignoring message from bot itself",
            extra={"operation": "bitrix.message", "result": "ignored"},
        )
        return
    
    logger.info(
        "Processing Bitrix message",
        extra={
            "operation": "bitrix.message",
            "result": "received",
            "dialog_id": dialog_id,
            "user_id": user_id,
            "message_length": len(message_text),
        },
    )
    
    # Парсинг ИНН из текста
    inn = extract_inn(message_text)
    
    if not inn:
        # Если ИНН не найден, отправляем подсказку
        await bitrix_client.send_message(
            dialog_id=dialog_id,
            message="❌ Не найден ИНН в вашем сообщении.\n"
                   "Пожалуйста, отправьте ИНН компании (10 или 12 цифр).\n\n"
                   "Пример: 7707083893"
        )
        return
    
    # Валидация ИНН
    if not validate_inn(inn):
        await bitrix_client.send_message(
            dialog_id=dialog_id,
            message=f"❌ Некорректный ИНН: {inn}\nПроверьте правильность ввода."
        )
        return
    
    # Отправка уведомления о начале обработки
    await bitrix_client.send_message(
        dialog_id=dialog_id,
        message=f"🔍 Ищу информацию по ИНН {inn}...\nПожалуйста, подождите."
    )
    
    try:
        # Получение данных из DaData
        company_data = await dadata_client.find_by_inn(inn)
        
        if not company_data:
            await bitrix_client.send_message(
                dialog_id=dialog_id,
                message=f"❌ Компания с ИНН {inn} не найдена в базе данных.\n"
                       "Проверьте правильность ИНН."
            )
            return
        
        # Анализ с помощью GPT
        # ВАЖНО: GPT формирует только выводы, все факты - из DaData
        analysis = await openai_client.analyze_company(company_data)
        
        # Формирование ответа
        response = _format_bitrix_response(company_data, analysis)
        
        # Отправка результата
        await bitrix_client.send_message(
            dialog_id=dialog_id,
            message=response
        )
    
    except Exception as e:
        logger.error(
            "Error processing INN in Bitrix",
            extra={"operation": "bitrix.inn", "result": "error", "inn": inn, "dialog_id": dialog_id},
            exc_info=True,
        )
        await bitrix_client.send_message(
            dialog_id=dialog_id,
            message=f"❌ Произошла ошибка при обработке запроса:\n{str(e)}\n\n"
                   "Пожалуйста, попробуйте позже."
        )


def _format_bitrix_response(company_data: Dict[str, Any], analysis: str) -> str:
    """
    Форматирование ответа для Bitrix24
    
    Args:
        company_data: Данные компании из DaData
        analysis: Анализ от GPT
        
    Returns:
        Отформатированный текст
    """
    parts = []
    
    # Заголовок
    parts.append("📊 ИНФОРМАЦИЯ О КОМПАНИИ\n")
    
    # Основные данные (только факты из DaData)
    parts.append(f"ИНН: {company_data.get('inn', 'не указан')}")
    parts.append(f"КПП: {company_data.get('kpp', 'не указан')}")
    parts.append(f"ОГРН: {company_data.get('ogrn', 'не указан')}")
    
    if company_data.get("name"):
        parts.append(f"Название: {company_data['name'].get('short', 'не указано')}")
    
    if company_data.get("state"):
        parts.append(f"Статус: {company_data['state'].get('status', 'не указан')}")
    
    parts.append("\n" + "="*40 + "\n")
    
    # Анализ от GPT (выводы и рекомендации)
    parts.append(analysis)
    
    return "\n".join(parts)
