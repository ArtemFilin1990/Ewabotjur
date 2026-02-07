"""Bitrix24 webhook and message handler."""

from __future__ import annotations

import json
import logging
from typing import Optional

from src.bot.schemas import TelegramMessage
from src.config import AppConfig
from src.integrations.bitrix24 import BitrixAPIClient, BitrixOAuthClient, BitrixTokens
from src.services.dadata import DaDataClient
from src.services.openai import generate_completion
from src.storage.bitrix_token_store import BitrixTokenStore


async def process_bitrix_event(
    event_data: dict,
    config: AppConfig,
    logger: logging.Logger,
    request_id: str,
) -> None:
    """
    Process Bitrix24 webhook event.
    
    Args:
        event_data: Event payload from Bitrix24
        config: Application configuration
        logger: Logger instance
        request_id: Request ID for tracking
    """
    event_type = event_data.get("event")
    
    if event_type == "ONIMBOTMESSAGEADD":
        await _handle_imbot_message(event_data, config, logger, request_id)
    else:
        logger.info(
            "bitrix event ignored",
            extra={
                "request_id": request_id,
                "event_type": event_type,
                "status": "ignored",
            }
        )


async def _handle_imbot_message(
    event_data: dict,
    config: AppConfig,
    logger: logging.Logger,
    request_id: str,
) -> None:
    """Handle incoming message from Bitrix24 imbot."""
    
    data = event_data.get("data", {})
    message_data = data.get("PARAMS", {})
    
    message_text = message_data.get("MESSAGE", "")
    dialog_id = message_data.get("DIALOG_ID", "")
    from_user_id = message_data.get("FROM_USER_ID", "")
    
    if not message_text or not dialog_id:
        logger.warning(
            "bitrix message missing required fields",
            extra={"request_id": request_id, "status": "invalid"},
        )
        return
    
    logger.info(
        "bitrix message received",
        extra={
            "request_id": request_id,
            "dialog_id": dialog_id,
            "status": "processing",
        }
    )
    
    # Extract INN from message text
    inn = _extract_inn(message_text)
    
    if not inn:
        await _send_bitrix_message(
            dialog_id,
            "Не удалось найти ИНН в сообщении. Пожалуйста, укажите ИНН (10 или 12 цифр).",
            config,
            logger,
            request_id,
        )
        return
    
    # Get company data from DaData
    if not config.dadata_token:
        await _send_bitrix_message(
            dialog_id,
            "DaData не настроена. Обратитесь к администратору.",
            config,
            logger,
            request_id,
        )
        return
    
    dadata_client = DaDataClient(
        config.dadata_token,
        config.dadata_secret,
        config.http_timeout_seconds,
    )
    
    try:
        company = await dadata_client.find_by_inn(inn)
    except Exception:
        logger.exception(
            "dadata lookup failed",
            extra={"request_id": request_id, "status": "error"},
        )
        await _send_bitrix_message(
            dialog_id,
            f"Ошибка при запросе данных из DaData. Код: {request_id}",
            config,
            logger,
            request_id,
        )
        return
    
    if not company:
        await _send_bitrix_message(
            dialog_id,
            f"Компания с ИНН {inn} не найдена в DaData.",
            config,
            logger,
            request_id,
        )
        return
    
    # Generate GPT analysis (conclusions only, no facts)
    if not config.openai_api_key:
        # Fallback: send only DaData facts without GPT analysis
        response = _format_company_facts(company)
    else:
        try:
            facts_text = _format_company_facts(company)
            analysis = await _generate_gpt_analysis(facts_text, config)
            response = f"{facts_text}\n\n📊 Анализ и рекомендации:\n{analysis}"
        except Exception:
            logger.exception(
                "gpt analysis failed",
                extra={"request_id": request_id, "status": "error"},
            )
            # Fallback to facts only
            response = _format_company_facts(company)
    
    await _send_bitrix_message(
        dialog_id,
        response,
        config,
        logger,
        request_id,
    )


def _extract_inn(text: str) -> Optional[str]:
    """
    Extract INN from text.
    
    Args:
        text: Message text
    
    Returns:
        INN if found, None otherwise
    """
    import re
    
    # Look for 10 or 12 digit numbers
    pattern = r'\b\d{10}(?:\d{2})?\b'
    matches = re.findall(pattern, text)
    
    if matches:
        # Return first match
        return matches[0]
    
    return None


def _format_company_facts(company) -> str:
    """
    Format company facts from DaData (NO GPT, only facts).
    
    Args:
        company: Company data from DaData
    
    Returns:
        Formatted facts string
    """
    lines = [
        "📋 Данные контрагента (DaData):",
        "",
        f"Название: {company.name or '—'}",
        f"ИНН: {company.inn or '—'}",
        f"ОГРН: {company.ogrn or '—'}",
        f"КПП: {company.kpp or '—'}",
        f"Адрес: {company.address or '—'}",
        f"Руководитель: {company.director or '—'}",
        f"Статус: {company.status or '—'}",
        f"Дата регистрации: {company.registration_date or '—'}",
    ]
    
    return "\n".join(lines)


async def _generate_gpt_analysis(facts: str, config: AppConfig) -> str:
    """
    Generate GPT analysis (conclusions and recommendations ONLY).
    
    Args:
        facts: Company facts from DaData
        config: Application configuration
    
    Returns:
        GPT analysis text
    """
    prompt = f"""На основе следующих ФАКТОВ о контрагенте из DaData, предоставь краткий анализ и рекомендации.

ВАЖНО:
- НЕ повторяй факты (название, ИНН, адрес и т.д.) - они уже есть
- Дай ТОЛЬКО выводы, риски и рекомендации
- Не выдумывай факты, которых нет в данных
- Объём: до 5-7 предложений

ФАКТЫ:
{facts}

Твой анализ:"""
    
    response = await generate_completion(
        prompt=prompt,
        api_key=config.openai_api_key,
        model=config.openai_model,
        temperature=config.openai_temperature,
        max_tokens=config.openai_max_tokens,
        timeout_seconds=config.http_timeout_seconds,
    )
    
    return response.get("content", "Анализ не сгенерирован.")


async def _send_bitrix_message(
    dialog_id: str,
    message: str,
    config: AppConfig,
    logger: logging.Logger,
    request_id: str,
) -> None:
    """
    Send message to Bitrix24 chat.
    
    Args:
        dialog_id: Chat/dialog ID
        message: Message text to send
        config: Application configuration
        logger: Logger instance
        request_id: Request ID for tracking
    """
    try:
        # Get tokens from storage
        token_store = BitrixTokenStore(config.memory_store_path)
        tokens = await token_store.get_tokens()
        
        if not tokens:
            logger.error(
                "bitrix tokens not found",
                extra={
                    "request_id": request_id,
                    "status": "error",
                    "message": "OAuth not completed",
                }
            )
            return
        
        # Check if token needs refresh
        oauth_client = BitrixOAuthClient(
            client_id=config.bitrix_client_id,
            client_secret=config.bitrix_client_secret,
            redirect_uri=config.bitrix_redirect_url,
            domain=config.bitrix_domain,
        )
        
        if oauth_client.is_token_expired(tokens):
            logger.info(
                "bitrix token expired, refreshing",
                extra={"request_id": request_id, "status": "refreshing"},
            )
            tokens = await oauth_client.refresh_access_token(
                tokens.refresh_token,
                config.http_timeout_seconds,
            )
            await token_store.save_tokens(tokens)
        
        # Send message
        api_client = BitrixAPIClient(tokens, config.http_timeout_seconds)
        await api_client.send_message(dialog_id, message)
        
        logger.info(
            "bitrix message sent",
            extra={
                "request_id": request_id,
                "dialog_id": dialog_id,
                "status": "success",
            }
        )
        
    except Exception:
        logger.exception(
            "failed to send bitrix message",
            extra={
                "request_id": request_id,
                "dialog_id": dialog_id,
                "status": "error",
            }
        )
