"""Deterministic scoring for company profiles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.services.dadata import CompanyProfile


@dataclass(slots=True)
class ScoreResult:
    """Scoring output for a company."""

    risk_level: str
    reasons: list[str]


def _parse_registration_date(raw_date: str | None) -> datetime | None:
    if not raw_date:
        return None
    try:
        return datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
    except ValueError:
        return None


def score_company(profile: CompanyProfile) -> ScoreResult:
    """Score company risk based on DaData profile."""

    reasons: list[str] = []
    risk_level = "LOW"

    if not profile.status or profile.status.upper() != "ACTIVE":
        risk_level = "HIGH"
        reasons.append("Статус компании не ACTIVE")

    if profile.mass_address:
        reasons.append("Массовый адрес")
        if risk_level == "LOW":
            risk_level = "MEDIUM"

    if profile.mass_director:
        reasons.append("Массовый директор")
        if risk_level != "HIGH":
            risk_level = "MEDIUM"

    if not profile.inn or not profile.ogrn or not profile.name:
        reasons.append("Отсутствуют критичные поля профиля")
        if risk_level == "LOW":
            risk_level = "MEDIUM"

    registration_date = _parse_registration_date(profile.registration_date)
    if registration_date:
        age_days = (datetime.now(timezone.utc) - registration_date).days
        if age_days < 180:
            reasons.append("Возраст компании менее 6 месяцев")
            if risk_level == "LOW":
                risk_level = "MEDIUM"

    if not reasons:
        reasons.append("Нет выявленных признаков риска")

    return ScoreResult(risk_level=risk_level, reasons=reasons)
