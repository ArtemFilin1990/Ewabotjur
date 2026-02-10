"""
Обработчик сообщений от Telegram
"""
import logging
from typing import Dict, Any, List

from src.config import settings
from src.utils.inn_parser import extract_inn, validate_inn
from src.integrations.dadata import dadata_client
from src.integrations.openai_client import openai_client
from src.utils.http import get_http_client

logger = logging.getLogger(__name__)


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
    parts.append("📊 **ИНФОРМАЦИЯ О КОМПАНИИ**\n")
    parts.append(f"**ИНН:** {company_data.get('inn', 'не указан')}")
    parts.append(f"**КПП:** {company_data.get('kpp', 'не указан')}")
    parts.append(f"**ОГРН:** {company_data.get('ogrn', 'не указан')}")
    parts.append(f"**Дата ОГРН:** {company_data.get('ogrn_date', 'не указана')}")
    parts.append(f"**HID:** {company_data.get('hid', 'не указан')}")
    parts.append(f"**Тип:** {company_data.get('type', 'не указан')}")
    
    if company_data.get("name"):
        parts.append(f"**Полное название:** {company_data['name'].get('full', 'не указано')}")
        parts.append(f"**Краткое название:** {company_data['name'].get('short', 'не указано')}")
        parts.append(f"**Название (латиница):** {company_data['name'].get('latin', 'не указано')}")
        parts.append(f"**Полное с ОПФ:** {company_data['name'].get('full_with_opf', 'не указано')}")
        parts.append(f"**Краткое с ОПФ:** {company_data['name'].get('short_with_opf', 'не указано')}")

    if company_data.get("opf"):
        opf = company_data["opf"]
        parts.append(f"**ОПФ код:** {opf.get('code', 'не указан')}")
        parts.append(f"**ОПФ полное:** {opf.get('full', 'не указано')}")
        parts.append(f"**ОПФ краткое:** {opf.get('short', 'не указано')}")

    if company_data.get("okved"):
        parts.append(f"**ОКВЭД:** {company_data['okved']}")
    parts.append(f"**Тип ОКВЭД:** {company_data.get('okved_type', 'не указан')}")
    parts.append(f"**ОКВЭДы:** {_format_okveds(company_data.get('okveds'))}")

    parts.append(f"**ОКПО:** {company_data.get('okpo', 'не указан')}")
    parts.append(f"**ОКАТО:** {company_data.get('okato', 'не указан')}")
    parts.append(f"**ОКТМО:** {company_data.get('oktmo', 'не указан')}")
    parts.append(f"**ОКОГУ:** {company_data.get('okogu', 'не указан')}")
    parts.append(f"**ОКФС:** {company_data.get('okfs', 'не указан')}")

    if company_data.get("address", {}).get("value"):
        parts.append(f"**Адрес:** {company_data['address']['value']}")
    if company_data.get("address", {}).get("unrestricted_value"):
        parts.append(f"**Адрес (полный):** {company_data['address']['unrestricted_value']}")
    parts.append(f"**Тип филиала:** {company_data.get('branch_type', 'не указан')}")
    parts.append(f"**Количество филиалов:** {company_data.get('branch_count', 'не указано')}")
    if company_data.get("capital"):
        parts.append(f"**Уставной капитал:** {company_data['capital']}")

    if company_data.get("management"):
        mgmt = company_data["management"]
        parts.append(
            f"**Руководитель:** {mgmt.get('name', 'не указан')} "
            f"({mgmt.get('post', 'должность не указана')})"
        )
    parts.append(f"**Менеджеры:** {_format_list(company_data.get('managers'))}")
    parts.append(f"**Учредители:** {_format_list(company_data.get('founders'))}")
    parts.append(f"**Контролирующие органы:** {_format_list(company_data.get('authorities'))}")
    parts.append(f"**Документы:** {_format_list(company_data.get('documents'))}")
    parts.append(f"**Предшественники:** {_format_list(company_data.get('predecessors'))}")
    parts.append(f"**Правопреемники:** {_format_list(company_data.get('successors'))}")
    parts.append(f"**Гражданство:** {company_data.get('citizenship', 'не указано')}")
    parts.append(f"**ФИО:** {company_data.get('fio', 'не указано')}")
    
    if company_data.get("state"):
        parts.append(f"**Статус:** {company_data['state'].get('status', 'не указан')}")
        parts.append(f"**Код статуса:** {company_data['state'].get('code', 'не указан')}")
        parts.append(f"**Дата актуальности:** {company_data['state'].get('actuality_date', 'не указана')}")

    if company_data.get("finance"):
        finance = company_data["finance"]
        parts.append("**Финансовые показатели:**")
        parts.append(f"- Выручка: {finance.get('revenue', 'нет данных')}")
        parts.append(f"- Расходы: {finance.get('expense', 'нет данных')}")
        parts.append(f"- Прибыль: {finance.get('profit', 'нет данных')}")
        parts.append(f"- Год: {finance.get('year', 'нет данных')}")
        parts.append(f"- Налоговый режим: {finance.get('tax_system', 'нет данных')}")
        parts.append(f"- Доход: {finance.get('income', 'нет данных')}")
        parts.append(f"- Долг: {finance.get('debt', 'нет данных')}")
        parts.append(f"- Пени: {finance.get('penalty', 'нет данных')}")
    else:
        parts.append("⚠️ **Финансовые данные недоступны на текущем тарифе DaData**")

    if company_data.get("employee_count"):
        parts.append(f"**Количество сотрудников:** {company_data['employee_count']}")
    parts.append(f"**Телефоны:** {_format_list(company_data.get('phones'))}")
    parts.append(f"**Email:** {_format_list(company_data.get('emails'))}")
    parts.append(f"**Лицензии:** {_format_licenses(company_data.get('licenses'))}")
    
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
        http_client = await get_http_client()
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
