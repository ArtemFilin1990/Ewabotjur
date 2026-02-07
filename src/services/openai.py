"""OpenAI GPT integration for company risk analysis."""

from __future__ import annotations

import asyncio
from typing import Optional
import httpx

from src.logging_config import get_logger


logger = get_logger(__name__)


class OpenAIError(RuntimeError):
    """Raised for OpenAI API errors."""


async def analyze_company_risks(
    company_data: dict,
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    timeout_seconds: float = 30.0,
) -> str:
    """
    Analyze company risks using OpenAI GPT.
    
    Args:
        company_data: Company profile data from DaData
        api_key: OpenAI API key
        model: Model name (default: gpt-4o-mini)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens in response (default: 2000)
        timeout_seconds: Request timeout (default: 30.0)
    
    Returns:
        Formatted risk analysis text
    
    Raises:
        OpenAIError: If API request fails
    """
    
    system_prompt = """Вы — юридический эксперт по анализу контрагентов.

Ваша задача: на основе ТОЛЬКО предоставленных данных из DaData:
1. Дать общую оценку компании (надёжность)
2. Перечислить выявленные риски
3. Рекомендовать, какие документы запросить у контрагента
4. Указать, что делать дальше

ВАЖНО:
- Используйте только факты из предоставленных данных
- Не придумывайте данные, которых нет
- Если каких-то данных нет — явно укажите это
- Если поле отсутствует в тарифе DaData — напишите "данные недоступны на вашем тарифе"
- Пишите кратко и структурированно"""

    user_prompt = f"""Проанализируйте контрагента на основе данных:

{_format_company_data(company_data)}

Предоставьте анализ в следующем формате:

**Общая оценка:**
[Ваша оценка надёжности]

**Выявленные риски:**
- [Риск 1]
- [Риск 2]
...

**Рекомендуемые документы для запроса:**
- [Документ 1]
- [Документ 2]
...

**Дальнейшие действия:**
[Что рекомендуете сделать]"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    timeout = httpx.Timeout(timeout_seconds)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        
        choices = data.get("choices", [])
        if not choices:
            raise OpenAIError("OpenAI returned empty choices")
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        if not content:
            raise OpenAIError("OpenAI returned empty content")
        
        logger.info(
            "openai analysis completed",
            extra={
                "module": "openai",
                "status": "success",
                "model": model,
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            },
        )
        
        return content.strip()
        
    except httpx.HTTPStatusError as exc:
        logger.error(
            "openai api error",
            extra={
                "module": "openai",
                "status": "error",
                "status_code": exc.response.status_code,
            },
        )
        raise OpenAIError(f"OpenAI API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        logger.error(
            "openai request error",
            extra={
                "module": "openai",
                "status": "error",
                "error_type": type(exc).__name__,
            },
        )
        raise OpenAIError("Failed to connect to OpenAI API") from exc


def _format_company_data(data: dict) -> str:
    """Format company data for GPT prompt."""
    
    lines = []
    
    if name := data.get("name"):
        lines.append(f"Название: {name}")
    
    if inn := data.get("inn"):
        lines.append(f"ИНН: {inn}")
    
    if ogrn := data.get("ogrn"):
        lines.append(f"ОГРН: {ogrn}")
    
    if kpp := data.get("kpp"):
        lines.append(f"КПП: {kpp}")
    
    if address := data.get("address"):
        lines.append(f"Адрес: {address}")
    
    if director := data.get("director"):
        lines.append(f"Руководитель: {director}")
    
    if status := data.get("status"):
        lines.append(f"Статус: {status}")
    
    if reg_date := data.get("registration_date"):
        lines.append(f"Дата регистрации: {reg_date}")
    
    if data.get("mass_address") is True:
        lines.append("⚠️ Массовый адрес регистрации")
    
    if data.get("mass_director") is True:
        lines.append("⚠️ Массовый руководитель")
    
    return "\n".join(lines) if lines else "Данные отсутствуют"
