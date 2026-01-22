"""Counterparty risk scoring service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

from src.services.dadata import CompanyProfile


@dataclass(frozen=True)
class RiskScore:
    """Risk score output."""

    level: str
    reasons: List[str]


def score_company(profile: CompanyProfile) -> RiskScore:
    """Compute a deterministic risk score for a company profile."""

    reasons: List[str] = []
    level = "LOW"

    if profile.status and profile.status.upper() != "ACTIVE":
        reasons.append("Статус компании не ACTIVE.")
        level = "HIGH"

    if profile.is_mass_address is True:
        reasons.append("Признак массового адреса.")
        level = "HIGH"

    if profile.is_mass_director is True:
        reasons.append("Признак массового руководителя.")
        if level != "HIGH":
            level = "MEDIUM"

    if _is_company_too_young(profile.registration_date):
        reasons.append("Компания зарегистрирована менее 6 месяцев назад.")
        if level == "LOW":
            level = "MEDIUM"

    missing_fields = [
        field_name
        for field_name, value in [
            ("название", profile.name),
            ("ИНН", profile.inn),
            ("ОГРН", profile.ogrn),
            ("адрес", profile.address),
            ("руководитель", profile.director),
        ]
        if not value
    ]
    if missing_fields:
        reasons.append(f"Отсутствуют критичные поля: {', '.join(missing_fields)}.")
        if level == "LOW":
            level = "MEDIUM"

    if not reasons:
        reasons.append("Критичных факторов риска не выявлено.")

    return RiskScore(level=level, reasons=reasons)


def _is_company_too_young(registration_date: str | None) -> bool:
    if not registration_date:
        return False
    try:
        created = datetime.fromisoformat(registration_date)
    except ValueError:
        return False
    return created.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc) - timedelta(days=180)
