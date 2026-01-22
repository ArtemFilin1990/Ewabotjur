"""DaData integration for company lookup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import datetime as dt

import httpx


@dataclass(frozen=True)
class CompanyProfile:
    """Normalized company profile."""

    name: Optional[str]
    inn: Optional[str]
    ogrn: Optional[str]
    kpp: Optional[str]
    address: Optional[str]
    director: Optional[str]
    status: Optional[str]
    registration_date: Optional[str]
    is_mass_address: Optional[bool]
    is_mass_director: Optional[bool]


class DadataError(RuntimeError):
    """Raised when DaData request fails."""


class DadataClient:
    """Client for DaData party lookup."""

    def __init__(
        self,
        token: str,
        secret: Optional[str],
        base_url: str,
        timeout_seconds: int,
    ) -> None:
        self._token = token
        self._secret = secret
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)

    def find_company_by_inn(self, inn: str) -> Optional[CompanyProfile]:
        """Fetch company profile by INN."""

        if not self._token:
            raise DadataError("DADATA_TOKEN is not configured")
        url = f"{self._base_url}/suggestions/api/4_1/rs/findById/party"
        headers = {"Authorization": f"Token {self._token}"}
        if self._secret:
            headers["X-Secret"] = self._secret

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, headers=headers, json={"query": inn})
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise DadataError(f"DaData request failed: {exc}") from exc

        suggestions = payload.get("suggestions", [])
        if not suggestions:
            return None
        data = suggestions[0].get("data", {})
        return _normalize_company_profile(data)


def _normalize_company_profile(data: Dict[str, Any]) -> CompanyProfile:
    name = _extract_name(data)
    registration_date = _format_registration_date(data)
    address_data = data.get("address") or {}
    address = address_data.get("unrestricted_value") or address_data.get("value")
    management = data.get("management") or {}
    is_mass_address = _first_present(
        data.get("is_mass_address"),
        (address_data.get("data") or {}).get("is_mass_address"),
    )
    is_mass_director = _first_present(
        data.get("is_mass_director"),
        management.get("is_mass"),
    )
    return CompanyProfile(
        name=name,
        inn=data.get("inn"),
        ogrn=data.get("ogrn"),
        kpp=data.get("kpp"),
        address=address,
        director=management.get("name"),
        status=(data.get("state") or {}).get("status"),
        registration_date=registration_date,
        is_mass_address=is_mass_address,
        is_mass_director=is_mass_director,
    )


def _extract_name(data: Dict[str, Any]) -> Optional[str]:
    name = data.get("name") or {}
    return name.get("full_with_opf") or name.get("short_with_opf") or data.get("value")


def _format_registration_date(data: Dict[str, Any]) -> Optional[str]:
    timestamp = (data.get("state") or {}).get("registration_date")
    if not timestamp:
        return None
    try:
        dt_value = dt.datetime.fromtimestamp(int(timestamp) / 1000, tz=dt.timezone.utc)
    except (ValueError, OSError):
        return None
    return dt_value.date().isoformat()


def _first_present(*values: Any) -> Optional[bool]:
    for value in values:
        if value is None:
            continue
        if isinstance(value, bool):
            return value
    return None
