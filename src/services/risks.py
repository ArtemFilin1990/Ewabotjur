"""Risk table generation for contract text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RiskRow:
    """Row for risks table."""

    index: int
    risk: str
    consequences: str
    probability: str
    impact: str
    mitigation: str


def build_risk_table(text: str) -> List[RiskRow]:
    """Create a deterministic risk table based on keyword heuristics."""

    if len(text.strip()) < 200:
        return [
            RiskRow(
                index=1,
                risk="ASSUMPTION: Недостаточно данных",
                consequences="TBD: отсутствует полный текст договора.",
                probability="TBD",
                impact="TBD",
                mitigation="Нужно: предмет, цена, сроки, ответственность, порядок расторжения.",
            )
        ]

    normalized = text.lower()
    rows: List[RiskRow] = []
    index = 1

    def add_row(risk: str, consequences: str, probability: str, impact: str, mitigation: str) -> None:
        nonlocal index
        rows.append(
            RiskRow(
                index=index,
                risk=risk,
                consequences=consequences,
                probability=probability,
                impact=impact,
                mitigation=mitigation,
            )
        )
        index += 1

    if "штраф" in normalized or "неустойк" in normalized:
        add_row(
            "Штрафы/неустойки",
            "Дополнительные финансовые потери.",
            "Средняя",
            "Высокое",
            "Проверить лимиты, предусмотреть взаимные штрафы.",
        )
    if "срок" in normalized or "дата" in normalized:
        add_row(
            "Сроки исполнения",
            "Срыв сроков и ответственность.",
            "Средняя",
            "Среднее",
            "Уточнить календарный план и ответственность сторон.",
        )
    if "конфиденц" in normalized:
        add_row(
            "Конфиденциальность",
            "Утечка данных и претензии.",
            "Низкая",
            "Высокое",
            "Зафиксировать режим информации и санкции.",
        )
    if "форс-мажор" in normalized or "непреодолим" in normalized:
        add_row(
            "Форс-мажор",
            "Приостановка обязательств.",
            "Низкая",
            "Среднее",
            "Проверить порядок уведомления и подтверждения.",
        )
    if not rows:
        add_row(
            "ASSUMPTION: Недостаточно данных",
            "Нужен полный текст договора.",
            "TBD",
            "TBD",
            "Запросить недостающий документ.",
        )
    return rows


def render_risk_table(rows: List[RiskRow]) -> str:
    """Render a markdown table for risks."""

    header = "| № | Риск | Последствия | Вероятность | Влияние | Меры реагирования |"
    separator = "|---|------|-------------|-------------|---------|-------------------|"
    lines = [header, separator]
    for row in rows:
        lines.append(
            f"| {row.index} | {row.risk} | {row.consequences} | {row.probability} | {row.impact} | {row.mitigation} |"
        )
    return "\n".join(lines)
