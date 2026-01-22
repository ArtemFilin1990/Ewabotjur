"""DaData integration for counterparty lookup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass(frozen=True)
class CompanyInfo:
    """Normalized company data from DaData."""

    inn: str
    name: str
    ogrn: Optional[str]
    kpp: Optional[str]
    address: Optional[str]
    director: Optional[str]
    status: Optional[str]
    registration_date: Optional[str]
    mass_address: Optional[bool]
    mass_director: Optional[bool]


class DaDataClient:
    """HTTP client for DaData party API."""

    def __init__(self, token: str, secret: Optional[str], timeout_seconds: int) -> None:
        self._token = token
        self._secret = secret
        self._timeout_seconds = timeout_seconds
        self._base_url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"

    async def find_by_inn(self, inn: str) -> Optional[CompanyInfo]:
        """Fetch company details by INN."""

        headers = {"Authorization": f"Token {self._token}"}
        if self._secret:
            headers["X-Secret"] = self._secret
        payload = {"query": inn}
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(self._base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        suggestions = data.get("suggestions", [])
        if not suggestions:
            return None
        return self._normalize_company(suggestions[0])

    def _normalize_company(self, payload: dict[str, Any]) -> CompanyInfo:
        data = payload.get("data", {})
        management = data.get("management") or {}
        address = data.get("address") or {}
        state = data.get("state") or {}
        return CompanyInfo(
            inn=data.get("inn", ""),
            name=payload.get("value") or data.get("name", {}).get("full_with_opf", ""),
            ogrn=data.get("ogrn"),
            kpp=data.get("kpp"),
            address=address.get("value"),
            director=management.get("name"),
            status=state.get("status"),
            registration_date=state.get("registration_date"),
            mass_address=data.get("mass_address"),
            mass_director=data.get("mass_director"),
        )
