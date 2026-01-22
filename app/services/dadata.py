"""DaData integration for company lookup."""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
from typing import Any

import httpx

from app.utils.logging import get_logger


DADATA_FIND_BY_ID_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
MAX_RETRIES = 2

logger = get_logger(__name__)


@dataclass(slots=True)
class CompanyProfile:
    """Structured company profile from DaData."""

    name: str | None
    inn: str | None
    ogrn: str | None
    kpp: str | None
    address: str | None
    director: str | None
    status: str | None
    registration_date: str | None
    mass_address: bool | None
    mass_director: bool | None


class DadataError(RuntimeError):
    """Raised for DaData API errors."""


async def fetch_company_profile(
    inn: str, token: str, secret: str | None, timeout_seconds: float
) -> CompanyProfile:
    """Fetch company profile from DaData by INN."""

    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if secret:
        headers["X-Secret"] = secret

    payload = {"query": inn}
    timeout = httpx.Timeout(timeout_seconds)
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    DADATA_FIND_BY_ID_URL, headers=headers, json=payload
                )
            response.raise_for_status()
            data = response.json()
            suggestions = data.get("suggestions") or []
            if not suggestions:
                raise DadataError("DaData returned empty suggestions list")

            suggestion = suggestions[0]
            data_fields: dict[str, Any] = suggestion.get("data") or {}
            # ASSUMPTION: DaData uses 'name.full_with_opf' and 'address.unrestricted_value'.
            name = (data_fields.get("name") or {}).get("full_with_opf")
            address = (data_fields.get("address") or {}).get("unrestricted_value")
            management = data_fields.get("management") or {}
            director = management.get("name")

            status = (data_fields.get("state") or {}).get("status")
            registration_date = (data_fields.get("state") or {}).get("registration_date")

            return CompanyProfile(
                name=name,
                inn=data_fields.get("inn"),
                ogrn=data_fields.get("ogrn"),
                kpp=data_fields.get("kpp"),
                address=address,
                director=director,
                status=status,
                registration_date=registration_date,
                mass_address=data_fields.get("mass_address"),
                mass_director=data_fields.get("mass_director"),
            )
        except (httpx.RequestError, httpx.HTTPStatusError, DadataError) as exc:
            last_error = exc
            logger.warning(
                "DaData request failed",
                extra={
                    "module": "dadata",
                    "status": "retry" if attempt < MAX_RETRIES else "failed",
                    "error_type": type(exc).__name__,
                },
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            break

    raise DadataError("Failed to fetch DaData profile") from last_error
