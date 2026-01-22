"""Deterministic contract risk analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
import re


@dataclass(frozen=True)
class RiskItem:
    """Single risk item."""

    risk: str
    consequences: str
    probability: str
    impact: str
    mitigation: str


@dataclass(frozen=True)
class RiskAnalysisResult:
    """Risk analysis output."""

    items: List[RiskItem]
    missing_information: List[str]


KEYWORD_RULES = [
    (
        re.compile(r"неустойк|штраф|пени", re.IGNORECASE),
        RiskItem(
            risk="Высокие штрафные санкции",
            consequences="Рост финансовых потерь при нарушении обязательств",
            probability="Средняя",
            impact="Высокое",
            mitigation="Уточнить лимиты штрафов и предусмотреть сроки устранения нарушений",
        ),
    ),
    (
        re.compile(r"односторонн", re.IGNORECASE),
        RiskItem(
            risk="Одностороннее расторжение",
            consequences="Контрагент может прекратить договор без компенсаций",
            probability="Средняя",
            impact="Среднее",
            mitigation="Согласовать условия уведомления и компенсации",
        ),
    ),
    (
        re.compile(r"конфиденциал|персональн|gdpr|152-фз", re.IGNORECASE),
        RiskItem(
            risk="Нарушение конфиденциальности/ПДн",
            consequences="Штрафы регуляторов и репутационные потери",
            probability="Низкая",
            impact="Высокое",
            mitigation="Прописать меры защиты и ответственность сторон",
        ),
    ),
    (
        re.compile(r"срок|deadline|этап", re.IGNORECASE),
        RiskItem(
            risk="Нереалистичные сроки исполнения",
            consequences="Срывы обязательств и штрафы",
            probability="Средняя",
            impact="Среднее",
            mitigation="Согласовать реалистичный график и порядок изменения сроков",
        ),
    ),
    (
        re.compile(r"оплат|аванс|предоплат", re.IGNORECASE),
        RiskItem(
            risk="Риск невозврата предоплаты",
            consequences="Потеря денежных средств при расторжении",
            probability="Средняя",
            impact="Среднее",
            mitigation="Определить условия возврата и этапы приемки",
        ),
    ),
]


MIN_TEXT_LENGTH = 200


def analyze_contract_risks(text: str) -> RiskAnalysisResult:
    """Analyze contract text and return a deterministic risk table."""

    normalized = (text or "").strip()
    if len(normalized) < MIN_TEXT_LENGTH:
        return RiskAnalysisResult(
            items=[
                RiskItem(
                    risk="TBD",
                    consequences="TBD",
                    probability="TBD",
                    impact="TBD",
                    mitigation="TBD",
                )
            ],
            missing_information=[
                "полный текст договора",
                "сведения о сторонах",
                "предмет договора",
                "условия оплаты",
                "сроки исполнения",
            ],
        )

    items: List[RiskItem] = []
    for pattern, item in KEYWORD_RULES:
        if pattern.search(normalized):
            items.append(item)

    if not items:
        items.append(
            RiskItem(
                risk="Недостаточно явных рисковых условий",
                consequences="Нужно подтверждение ключевых условий договора",
                probability="TBD",
                impact="TBD",
                mitigation="Уточнить предмет, оплату, сроки и ответственность",
            )
        )

    return RiskAnalysisResult(items=items, missing_information=[])


def format_risk_table(result: RiskAnalysisResult) -> str:
    """Format a Markdown table with risk items."""

    header = "| № | Риск | Последствия | Вероятность | Влияние | Меры реагирования |"
    separator = "| --- | --- | --- | --- | --- | --- |"
    rows = [
        f"| {index + 1} | {item.risk} | {item.consequences} | {item.probability} | {item.impact} | {item.mitigation} |"
        for index, item in enumerate(result.items)
    ]
    return "\n".join([header, separator, *rows])
