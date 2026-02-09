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
    parts = []
    parts.append("📊 **ИНФОРМАЦИЯ О КОМПАНИИ**\n")

    # Основные реквизиты
    parts.append(f"**ИНН:** {company_data.get('inn', 'не указан')}")
    parts.append(f"**КПП:** {company_data.get('kpp', 'не указан')}")
    parts.append(f"**ОГРН:** {company_data.get('ogrn', 'не указан')}")
    if company_data.get("ogrn_date"):
        parts.append(f"**Дата ОГРН:** {company_data['ogrn_date']}")

    # Наименование
    name = company_data.get("name") or {}
    if name.get("short_with_opf"):
        parts.append(f"**Название:** {name['short_with_opf']}")
    elif name.get("full_with_opf"):
        parts.append(f"**Название:** {name['full_with_opf']}")
    if name.get("latin"):
        parts.append(f"**Латинское:** {name['latin']}")

    # ОПФ
    opf = company_data.get("opf") or {}
    if opf.get("full"):
        parts.append(f"**ОПФ:** {opf['full']}")

    # Тип
    if company_data.get("type"):
        parts.append(f"**Тип:** {company_data['type']}")

    # Статус
    state = company_data.get("state") or {}
    if state.get("status"):
        parts.append(f"**Статус:** {state['status']}")
    if state.get("registration_date"):
        parts.append(f"**Дата регистрации:** {state['registration_date']}")
    if state.get("liquidation_date"):
        parts.append(f"**Дата ликвидации:** {state['liquidation_date']}")
    if state.get("actuality_date"):
        parts.append(f"**Актуальность:** {state['actuality_date']}")

    # Адрес
    address = company_data.get("address") or {}
    if address.get("value"):
        parts.append(f"**Адрес:** {address['value']}")

    # Руководство
    mgmt = company_data.get("management")
    if mgmt:
        parts.append(f"**Руководитель:** {mgmt.get('name', '—')} ({mgmt.get('post', '—')})")

    # Уставный капитал
    capital = company_data.get("capital")
    if capital:
        parts.append(f"**Уставный капитал:** {capital.get('value', '—')} ({capital.get('type', '')})")

    # ОКВЭД
    if company_data.get("okved"):
        parts.append(f"**ОКВЭД (основной):** {company_data['okved']}")
    okveds = company_data.get("okveds")
    if okveds:
        extra = [o.get("code", "") for o in okveds if not o.get("main")]
        if extra:
            parts.append(f"**ОКВЭД (доп.):** {', '.join(extra[:10])}")
            if len(extra) > 10:
                parts.append(f"   ...и ещё {len(extra) - 10}")

    # Классификаторы
    codes = []
    for code_name, label in [("okpo", "ОКПО"), ("okato", "ОКАТО"),
                             ("oktmo", "ОКТМО"), ("okogu", "ОКОГУ"),
                             ("okfs", "ОКФС")]:
        val = company_data.get(code_name)
        if val:
            codes.append(f"{label}: {val}")
    if codes:
        parts.append(f"**Коды:** {', '.join(codes)}")

    # Филиалы
    if company_data.get("branch_type"):
        parts.append(f"**Тип филиала:** {company_data['branch_type']}")
    if company_data.get("branch_count"):
        parts.append(f"**Кол-во филиалов:** {company_data['branch_count']}")

    # Сотрудники
    if company_data.get("employee_count") is not None:
        parts.append(f"**Сотрудники:** {company_data['employee_count']}")

    # Финансы
    finance = company_data.get("finance")
    if finance:
        parts.append("\n💰 **ФИНАНСЫ**")
        if finance.get("year"):
            parts.append(f"**Год:** {finance['year']}")
        if finance.get("tax_system"):
            parts.append(f"**Система налогообложения:** {finance['tax_system']}")
        if finance.get("revenue") is not None:
            parts.append(f"**Выручка:** {finance['revenue']}")
        if finance.get("income") is not None:
            parts.append(f"**Доход:** {finance['income']}")
        if finance.get("expense") is not None:
            parts.append(f"**Расходы:** {finance['expense']}")
        if finance.get("debt") is not None:
            parts.append(f"**Задолженность:** {finance['debt']}")
        if finance.get("penalty") is not None:
            parts.append(f"**Штрафы:** {finance['penalty']}")

    # Учредители
    founders = company_data.get("founders")
    if founders:
        parts.append("\n👥 **УЧРЕДИТЕЛИ**")
        for f in founders[:5]:
            fname = f.get("name") or ""
            fio = f.get("fio")
            if fio:
                fname = " ".join(
                    filter(None, [fio.get("surname"), fio.get("name"), fio.get("patronymic")])
                ) or fname
            share = f.get("share")
            share_str = ""
            if share and share.get("value"):
                share_str = f" ({share['value']}%)" if share.get("type") == "PERCENT" else f" (доля: {share['value']})"
            parts.append(f"  • {fname}{share_str}")
        if len(founders) > 5:
            parts.append(f"  ...и ещё {len(founders) - 5}")

    # Руководители (managers)
    managers = company_data.get("managers")
    if managers:
        parts.append("\n👔 **РУКОВОДИТЕЛИ**")
        for m in managers[:5]:
            mname = m.get("name") or ""
            fio = m.get("fio")
            if fio:
                mname = " ".join(
                    filter(None, [fio.get("surname"), fio.get("name"), fio.get("patronymic")])
                ) or mname
            post = m.get("post", "")
            parts.append(f"  • {mname} — {post}")
        if len(managers) > 5:
            parts.append(f"  ...и ещё {len(managers) - 5}")

    # Лицензии
    licenses = company_data.get("licenses")
    if licenses:
        parts.append(f"\n📜 **ЛИЦЕНЗИИ** ({len(licenses)})")
        for lic in licenses[:3]:
            num = lic.get("number", "—")
            activities = lic.get("activities") or []
            act_str = activities[0] if len(activities) > 0 else ""
            parts.append(f"  • №{num} {act_str}")
        if len(licenses) > 3:
            parts.append(f"  ...и ещё {len(licenses) - 3}")

    # Контакты
    phones = company_data.get("phones")
    if phones:
        parts.append(f"**Телефоны:** {', '.join(phones[:5])}")
    emails = company_data.get("emails")
    if emails:
        parts.append(f"**Email:** {', '.join(emails[:5])}")

    # Правопредшественники / правопреемники
    predecessors = company_data.get("predecessors")
    if predecessors:
        parts.append("\n🔄 **Правопредшественники:**")
        for p in predecessors[:3]:
            parts.append(f"  • {p.get('name', '—')} (ИНН {p.get('inn', '—')})")

    successors = company_data.get("successors")
    if successors:
        parts.append("\n🔄 **Правопреемники:**")
        for s in successors[:3]:
            parts.append(f"  • {s.get('name', '—')} (ИНН {s.get('inn', '—')})")

    parts.append("\n" + "=" * 40 + "\n")
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