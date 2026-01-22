"""Risk scoring for counterparties."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from src.services.dadata import CompanyInfo


@dataclass(frozen=True)
class ScoreResult:
    """Scoring result for a counterparty."""

    level: str
    reasons: List[str]


CRITICAL_FIELDS = ("name", "ogrn", "kpp", "address", "director", "registration_date")


def validate_inn(inn: str) -> bool:
    """Validate INN format (10 or 12 digits)."""

    return inn.isdigit() and len(inn) in {10, 12}


def score_company(company: CompanyInfo) -> ScoreResult:
    """Calculate a deterministic base risk score for a company."""

    reasons: List[str] = []
    high_risk = False
    medium_risk = False

    if company.status and company.status.upper() != "ACTIVE":
        reasons.append(f"Статус компании: {company.status}")
        high_risk = True

    if company.mass_address is True:
        reasons.append("Признак массового адреса")
        medium_risk = True

    if company.mass_director is True:
        reasons.append("Признак массового руководителя")
        medium_risk = True

    if _is_recent_company(company.registration_date, months=6):
        reasons.append("Компания зарегистрирована менее 6 месяцев назад")
        medium_risk = True

    missing_fields = _missing_fields(company)
    if missing_fields:
        reasons.append(f"Отсутствуют поля: {', '.join(missing_fields)}")
        medium_risk = True

    if high_risk:
        level = "HIGH"
    elif medium_risk:
        level = "MEDIUM"
    else:
        level = "LOW"

    return ScoreResult(level=level, reasons=reasons)


def _missing_fields(company: CompanyInfo) -> List[str]:
    missing: List[str] = []
    for field in CRITICAL_FIELDS:
        if getattr(company, field) in (None, "", []):
            missing.append(field)
    return missing


def _is_recent_company(registration_date: Optional[str], months: int) -> bool:
    if not registration_date:
        return False
    try:
        if registration_date.isdigit():
            timestamp = int(registration_date) / 1000
            registered_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            registered_at = datetime.fromisoformat(registration_date)
    except ValueError:
        return False
    delta = datetime.now(timezone.utc) - registered_at
    return delta.days <= months * 30
