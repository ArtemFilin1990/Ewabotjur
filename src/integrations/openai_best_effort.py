"""Best-effort OpenAI client used for optional summaries."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import settings
from src.utils.http import get_http_client

logger = logging.getLogger(__name__)


class OpenAIBestEffortClient:
    BASE_URL = "https://api.openai.com/v1/chat/completions"

    async def summarize(self, company_payload: dict[str, Any], risk_summary: str) -> str | None:
        if not settings.openai_api_key:
            return None

        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": "Дай краткое бизнес-резюме рисков (до 7 предложений)."},
                {"role": "user", "content": f"Риски: {risk_summary}\nДанные: {company_payload}"},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
        }
        try:
            client = await get_http_client()
            response = await client.post(
                self.BASE_URL,
                json=payload,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError):
            logger.warning(
                "OpenAI summary unavailable",
                extra={"operation": "openai.summary", "result": "warning"},
                exc_info=True,
            )
            return None


openai_best_effort_client = OpenAIBestEffortClient()
