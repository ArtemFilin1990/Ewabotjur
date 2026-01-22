"""DaData integration service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
import httpx


@dataclass(frozen=True)
class CompanyCard:
    """Normalized company data from DaData."""

    name: str
    inn: str
    ogrn: Optional[str]
    kpp: Optional[str]
    address: Optional[str]
    director: Optional[str]
    status: Optional[str]
    registration_date: Optional[datetime]
    raw_flags: dict[str, Any]


class DaDataError(RuntimeError):
    """DaData API error."""


class DaDataService:
    """Service for querying DaData party API."""

    def __init__(self, token: Optional[str], secret: Optional[str], timeout: int) -> None:
        self._token = token
        self._secret = secret
        self._timeout = timeout

    async def find_company_by_inn(self, inn: str) -> Optional[CompanyCard]:
        """Find company card by INN."""

        if not self._token:
            raise DaDataError("DADATA_TOKEN is not configured")

        url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
        headers = {"Authorization": f"Token {self._token}"}
        if self._secret:
            headers["X-Secret"] = self._secret

        payload = {"query": inn}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise DaDataError(f"DaData error: {response.status_code} {response.text}")

        data = response.json()
        suggestions = data.get("suggestions", [])
        if not suggestions:
            return None

        suggestion = suggestions[0]
        value = suggestion.get("value") or ""
        raw_data = suggestion.get("data", {})
        name = (
            raw_data.get("name", {}).get("full_with_opf")
            or raw_data.get("name", {}).get("short_with_opf")
            or value
        )
        registration_date = _parse_date(raw_data.get("ogrn_date"))
        director = None
        management = raw_data.get("management")
        if isinstance(management, dict):
            director = management.get("name")

        address = None
        if isinstance(raw_data.get("address"), dict):
            address = raw_data["address"].get("value")

        status = None
        if isinstance(raw_data.get("state"), dict):
            status = raw_data["state"].get("status")

        raw_flags = {
            "address_data": raw_data.get("address", {}).get("data")
            if isinstance(raw_data.get("address"), dict)
            else None,
            "management": management,
            "state": raw_data.get("state"),
        }

        return CompanyCard(
            name=name,
            inn=raw_data.get("inn") or inn,
            ogrn=raw_data.get("ogrn"),
            kpp=raw_data.get("kpp"),
            address=address,
            director=director,
            status=status,
            registration_date=registration_date,
            raw_flags=raw_flags,
        )


def _parse_date(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        timestamp = int(value) / 1000
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)
