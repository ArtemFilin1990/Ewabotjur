"""Deterministic scoring for counterparty risk."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src.services.dadata_service import CompanyCard


@dataclass(frozen=True)
class RiskAssessment:
    """Risk assessment result."""

    level: str
    reasons: list[str]


class RiskScoringService:
    """Service for evaluating company risk level."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    def evaluate(self, company: CompanyCard) -> RiskAssessment:
        """Evaluate risk level based on DaData fields."""

        reasons: list[str] = []
        level = self.LOW

        if company.status and company.status.upper() != "ACTIVE":
            reasons.append(f"Статус компании: {company.status}")
            level = self.HIGH

        if _is_missing_critical(company):
            reasons.append("Недостаточно критичных реквизитов (ОГРН/КПП/адрес)")
            level = self._raise_level(level, self.MEDIUM)

        if _is_too_young(company.registration_date):
            reasons.append("Компания зарегистрирована менее 6 месяцев назад")
            level = self._raise_level(level, self.MEDIUM)

        mass_reasons = _detect_mass_flags(company.raw_flags)
        if mass_reasons:
            reasons.extend(mass_reasons)
            level = self._raise_level(level, self.MEDIUM)

        if not reasons:
            reasons.append("Критичных факторов риска не выявлено")

        return RiskAssessment(level=level, reasons=reasons)

    @staticmethod
    def _raise_level(current: str, candidate: str) -> str:
        order = {RiskScoringService.LOW: 1, RiskScoringService.MEDIUM: 2, RiskScoringService.HIGH: 3}
        return candidate if order[candidate] > order[current] else current


def _is_missing_critical(company: CompanyCard) -> bool:
    return not (company.ogrn and company.kpp and company.address)


def _is_too_young(registration_date: Optional[datetime]) -> bool:
    if registration_date is None:
        return False
    threshold = datetime.now(tz=timezone.utc) - timedelta(days=180)
    return registration_date >= threshold


def _detect_mass_flags(flags: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    address_data = flags.get("address_data")
    if isinstance(address_data, dict) and address_data.get("is_mass"):
        reasons.append("Отмечен признак массового адреса")

    management = flags.get("management")
    if isinstance(management, dict) and management.get("is_mass"):
        reasons.append("Отмечен признак массового руководителя")

    state = flags.get("state")
    if isinstance(state, dict) and state.get("liquidation_date"):
        reasons.append("Обнаружены признаки ликвидации")

    return reasons
