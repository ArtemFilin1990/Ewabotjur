"""Deterministic risk scoring from DaData fields."""
from __future__ import annotations

from typing import Any


def build_risk_assessment(company_data: dict[str, Any]) -> tuple[float, list[str], str]:
    payload = company_data.get("data") or {}
    state = payload.get("state") or {}
    score = 0.0
    flags: list[str] = []

    if payload.get("invalid"):
        score += 35
        flags.append("Компания помечена как недостоверная")

    status = state.get("status")
    if status in {"LIQUIDATING", "LIQUIDATED", "BANKRUPT"}:
        score += 40
        flags.append(f"Негативный статус ЕГРЮЛ: {status}")

    finance = payload.get("finance") or {}
    if finance:
        debt = float(finance.get("debt") or 0)
        revenue = float(finance.get("revenue") or 0)
        if debt > 0:
            score += min(20, debt / 1_000_000)
            flags.append("Обнаружена налоговая задолженность")
        if revenue == 0:
            score += 10
            flags.append("Нет данных о выручке")
    else:
        flags.append("Финансовые данные недоступны")

    if not payload.get("licenses"):
        flags.append("Лицензии не обнаружены")

    if not payload.get("management"):
        score += 10
        flags.append("Нет данных о руководителе")

    score = min(100.0, round(score, 1))
    summary = f"Риск-скор: {score}/100. " + ("; ".join(flags) if flags else "Критичные флаги не найдены")
    return score, flags, summary
