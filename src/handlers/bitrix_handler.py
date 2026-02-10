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

    # Ограничение длины входящего текста для защиты от атак
    if len(message_text) > 1000:
        logger.warning(
            "Message too long",
            extra={"operation": "bitrix.message", "result": "rejected", "length": len(message_text)},
        )
        await bitrix_client.send_message(
            dialog_id=dialog_id,
            message="❌ Сообщение слишком длинное. Пожалуйста, отправьте ИНН (10 или 12 цифр)."
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
    def _format_list(values: Any) -> str:
        if not values:
            return "не указано"
        if isinstance(values, list):
            return ", ".join(str(item) for item in values if item is not None) or "не указано"
        return str(values)

    def _format_okveds(okveds: Any) -> str:
        if not okveds:
            return "не указано"
        formatted = []
        for entry in okveds:
            if isinstance(entry, dict):
                code = entry.get("code")
                name = entry.get("name")
                if code and name:
                    formatted.append(f"{code} — {name}")
                elif code:
                    formatted.append(str(code))
                elif name:
                    formatted.append(str(name))
            else:
                formatted.append(str(entry))
        return "; ".join(formatted) if formatted else "не указано"

    def _format_licenses(licenses: Any) -> str:
        if not licenses:
            return "не указано"
        formatted = []
        for license_item in licenses:
            if not isinstance(license_item, dict):
                formatted.append(str(license_item))
                continue
            number = license_item.get("number") or "не указан"
            issue_date = license_item.get("issue_date") or "не указана"
            expire_date = license_item.get("expire_date") or "не указана"
            activities = license_item.get("activities") or []
            activities_text = _format_list(activities)
            formatted.append(
                f"№ {number}, выдача: {issue_date}, окончание: {expire_date}, виды: {activities_text}"
            )
        return "; ".join(formatted) if formatted else "не указано"

    parts = []
    
    # Заголовок
    parts.append("📊 ИНФОРМАЦИЯ О КОМПАНИИ\n")
    
    # Основные данные (только факты из DaData)
    parts.append(f"ИНН: {company_data.get('inn', 'не указан')}")
    parts.append(f"КПП: {company_data.get('kpp', 'не указан')}")
    parts.append(f"ОГРН: {company_data.get('ogrn', 'не указан')}")
    parts.append(f"Дата ОГРН: {company_data.get('ogrn_date', 'не указана')}")
    parts.append(f"HID: {company_data.get('hid', 'не указан')}")
    parts.append(f"Тип: {company_data.get('type', 'не указан')}")
    
    if company_data.get("name"):
        parts.append(f"Полное название: {company_data['name'].get('full', 'не указано')}")
        parts.append(f"Краткое название: {company_data['name'].get('short', 'не указано')}")
        parts.append(f"Название (латиница): {company_data['name'].get('latin', 'не указано')}")
        parts.append(f"Полное с ОПФ: {company_data['name'].get('full_with_opf', 'не указано')}")
        parts.append(f"Краткое с ОПФ: {company_data['name'].get('short_with_opf', 'не указано')}")

    if company_data.get("opf"):
        opf = company_data["opf"]
        parts.append(f"ОПФ код: {opf.get('code', 'не указан')}")
        parts.append(f"ОПФ полное: {opf.get('full', 'не указано')}")
        parts.append(f"ОПФ краткое: {opf.get('short', 'не указано')}")

    if company_data.get("okved"):
        parts.append(f"ОКВЭД: {company_data['okved']}")
    parts.append(f"Тип ОКВЭД: {company_data.get('okved_type', 'не указан')}")
    parts.append(f"ОКВЭДы: {_format_okveds(company_data.get('okveds'))}")

    parts.append(f"ОКПО: {company_data.get('okpo', 'не указан')}")
    parts.append(f"ОКАТО: {company_data.get('okato', 'не указан')}")
    parts.append(f"ОКТМО: {company_data.get('oktmo', 'не указан')}")
    parts.append(f"ОКОГУ: {company_data.get('okogu', 'не указан')}")
    parts.append(f"ОКФС: {company_data.get('okfs', 'не указан')}")

    if company_data.get("address", {}).get("value"):
        parts.append(f"Адрес: {company_data['address']['value']}")
    if company_data.get("address", {}).get("unrestricted_value"):
        parts.append(f"Адрес (полный): {company_data['address']['unrestricted_value']}")
    parts.append(f"Тип филиала: {company_data.get('branch_type', 'не указан')}")
    parts.append(f"Количество филиалов: {company_data.get('branch_count', 'не указано')}")
    if company_data.get("capital"):
        parts.append(f"Уставной капитал: {company_data['capital']}")

    if company_data.get("management"):
        mgmt = company_data["management"]
        parts.append(
            f"Руководитель: {mgmt.get('name', 'не указан')} "
            f"({mgmt.get('post', 'должность не указана')})"
        )
    parts.append(f"Менеджеры: {_format_list(company_data.get('managers'))}")
    parts.append(f"Учредители: {_format_list(company_data.get('founders'))}")
    parts.append(f"Контролирующие органы: {_format_list(company_data.get('authorities'))}")
    parts.append(f"Документы: {_format_list(company_data.get('documents'))}")
    parts.append(f"Предшественники: {_format_list(company_data.get('predecessors'))}")
    parts.append(f"Правопреемники: {_format_list(company_data.get('successors'))}")
    parts.append(f"Гражданство: {company_data.get('citizenship', 'не указано')}")
    parts.append(f"ФИО: {company_data.get('fio', 'не указано')}")
    
    if company_data.get("state"):
        parts.append(f"Статус: {company_data['state'].get('status', 'не указан')}")
        parts.append(f"Код статуса: {company_data['state'].get('code', 'не указан')}")
        parts.append(f"Дата актуальности: {company_data['state'].get('actuality_date', 'не указана')}")

    if company_data.get("finance"):
        finance = company_data["finance"]
        parts.append("Финансовые показатели:")
        parts.append(f"- Выручка: {finance.get('revenue', 'нет данных')}")
        parts.append(f"- Расходы: {finance.get('expense', 'нет данных')}")
        parts.append(f"- Прибыль: {finance.get('profit', 'нет данных')}")
        parts.append(f"- Год: {finance.get('year', 'нет данных')}")
        parts.append(f"- Налоговый режим: {finance.get('tax_system', 'нет данных')}")
        parts.append(f"- Доход: {finance.get('income', 'нет данных')}")
        parts.append(f"- Долг: {finance.get('debt', 'нет данных')}")
        parts.append(f"- Пени: {finance.get('penalty', 'нет данных')}")
    else:
        parts.append("⚠️ Финансовые данные недоступны на текущем тарифе DaData")

    if company_data.get("employee_count"):
        parts.append(f"Количество сотрудников: {company_data['employee_count']}")
    parts.append(f"Телефоны: {_format_list(company_data.get('phones'))}")
    parts.append(f"Email: {_format_list(company_data.get('emails'))}")
    parts.append(f"Лицензии: {_format_licenses(company_data.get('licenses'))}")
    
    parts.append("\n" + "="*40 + "\n")
    
    # Анализ от GPT (выводы и рекомендации)
    parts.append(analysis)
    
    return "\n".join(parts)
