"""DaData integration for findById/party and findAffiliated/party."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import settings
from src.utils.http import get_http_client

logger = logging.getLogger(__name__)


class DaDataClient:
    BASE_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"

    def __init__(self) -> None:
        self.headers = {
            "Authorization": f"Token {settings.dadata_api_key}",
            "X-Secret": settings.dadata_secret_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def find_party(self, inn: str) -> dict[str, Any] | None:
        data = await self._post("findById/party", {"query": inn})
        suggestions = data.get("suggestions") or []
        return suggestions[0] if suggestions else None

    async def find_affiliated(self, inn: str) -> dict[str, Any] | None:
        try:
            data = await self._post("findAffiliated/party", {"query": inn})
            return data
        except httpx.HTTPStatusError:
            logger.warning(
                "Affiliated lookup skipped",
                extra={"operation": "dadata.find_affiliated", "result": "warning", "inn": inn},
                exc_info=True,
            )
            return None

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = await get_http_client()
        response = await client.post(
            f"{self.BASE_URL}/{path}",
            json=payload,
            headers=self.headers,
            timeout=settings.http_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()


dadata_client = DaDataClient()
