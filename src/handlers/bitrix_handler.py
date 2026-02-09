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
    parts = []

    parts.append("📊 ИНФОРМАЦИЯ О КОМПАНИИ\n")

    # Основные реквизиты
    parts.append(f"ИНН: {company_data.get('inn', 'не указан')}")
    parts.append(f"КПП: {company_data.get('kpp', 'не указан')}")
    parts.append(f"ОГРН: {company_data.get('ogrn', 'не указан')}")
    if company_data.get("ogrn_date"):
        parts.append(f"Дата ОГРН: {company_data['ogrn_date']}")

    # Наименование
    name = company_data.get("name") or {}
    if name.get("short_with_opf"):
        parts.append(f"Название: {name['short_with_opf']}")
    elif name.get("full_with_opf"):
        parts.append(f"Название: {name['full_with_opf']}")
    if name.get("latin"):
        parts.append(f"Латинское: {name['latin']}")

    # ОПФ
    opf = company_data.get("opf") or {}
    if opf.get("full"):
        parts.append(f"ОПФ: {opf['full']}")

    # Тип
    if company_data.get("type"):
        parts.append(f"Тип: {company_data['type']}")

    # Статус
    state = company_data.get("state") or {}
    if state.get("status"):
        parts.append(f"Статус: {state['status']}")
    if state.get("registration_date"):
        parts.append(f"Дата регистрации: {state['registration_date']}")
    if state.get("liquidation_date"):
        parts.append(f"Дата ликвидации: {state['liquidation_date']}")
    if state.get("actuality_date"):
        parts.append(f"Актуальность: {state['actuality_date']}")

    # Адрес
    address = company_data.get("address") or {}
    if address.get("value"):
        parts.append(f"Адрес: {address['value']}")

    # Руководство
    mgmt = company_data.get("management")
    if mgmt:
        parts.append(f"Руководитель: {mgmt.get('name', '—')} ({mgmt.get('post', '—')})")

    # Уставный капитал
    capital = company_data.get("capital")
    if capital:
        parts.append(f"Уставный капитал: {capital.get('value', '—')} ({capital.get('type', '')})")

    # ОКВЭД
    if company_data.get("okved"):
        parts.append(f"ОКВЭД (основной): {company_data['okved']}")
    okveds = company_data.get("okveds")
    if okveds:
        extra = [o.get("code", "") for o in okveds if not o.get("main")]
        if extra:
            parts.append(f"ОКВЭД (доп.): {', '.join(extra[:10])}")
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
        parts.append(f"Коды: {', '.join(codes)}")

    # Филиалы
    if company_data.get("branch_type"):
        parts.append(f"Тип филиала: {company_data['branch_type']}")
    if company_data.get("branch_count"):
        parts.append(f"Кол-во филиалов: {company_data['branch_count']}")

    # Сотрудники
    if company_data.get("employee_count") is not None:
        parts.append(f"Сотрудники: {company_data['employee_count']}")

    # Финансы
    finance = company_data.get("finance")
    if finance:
        parts.append("\n💰 ФИНАНСЫ")
        if finance.get("year"):
            parts.append(f"Год: {finance['year']}")
        if finance.get("tax_system"):
            parts.append(f"Система налогообложения: {finance['tax_system']}")
        if finance.get("revenue") is not None:
            parts.append(f"Выручка: {finance['revenue']}")
        if finance.get("income") is not None:
            parts.append(f"Доход: {finance['income']}")
        if finance.get("expense") is not None:
            parts.append(f"Расходы: {finance['expense']}")
        if finance.get("debt") is not None:
            parts.append(f"Задолженность: {finance['debt']}")
        if finance.get("penalty") is not None:
            parts.append(f"Штрафы: {finance['penalty']}")

    # Учредители
    founders = company_data.get("founders")
    if founders:
        parts.append("\n👥 УЧРЕДИТЕЛИ")
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
        parts.append("\n👔 РУКОВОДИТЕЛИ")
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
        parts.append(f"\n📜 ЛИЦЕНЗИИ ({len(licenses)})")
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
        parts.append(f"Телефоны: {', '.join(phones[:5])}")
    emails = company_data.get("emails")
    if emails:
        parts.append(f"Email: {', '.join(emails[:5])}")

    # Правопредшественники / правопреемники
    predecessors = company_data.get("predecessors")
    if predecessors:
        parts.append("\n🔄 Правопредшественники:")
        for p in predecessors[:3]:
            parts.append(f"  • {p.get('name', '—')} (ИНН {p.get('inn', '—')})")

    successors = company_data.get("successors")
    if successors:
        parts.append("\n🔄 Правопреемники:")
        for s in successors[:3]:
            parts.append(f"  • {s.get('name', '—')} (ИНН {s.get('inn', '—')})")

    parts.append("\n" + "=" * 40 + "\n")
    parts.append(analysis)

    return "\n".join(parts)
