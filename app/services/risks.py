"""Deterministic risks analysis for contract text."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class RiskTemplate:
    """Template for risk extraction."""

    keyword: str
    risk: str
    consequences: str
    mitigation: str


RISK_TEMPLATES = [
    RiskTemplate(
        keyword="штраф",
        risk="Штрафные санкции",
        consequences="Финансовые потери при нарушении обязательств",
        mitigation="Проверить условия неустойки и лимиты",
    ),
    RiskTemplate(
        keyword="неустойк",
        risk="Неустойка за просрочку",
        consequences="Увеличение суммы обязательств",
        mitigation="Согласовать сроки и исключения",
    ),
    RiskTemplate(
        keyword="односторонн",
        risk="Односторонний отказ",
        consequences="Потеря договора без компенсации",
        mitigation="Добавить условия уведомления и компенсации",
    ),
    RiskTemplate(
        keyword="конфиденц",
        risk="Нарушение конфиденциальности",
        consequences="Риски утечки данных и штрафов",
        mitigation="Уточнить перечень данных и режим доступа",
    ),
    RiskTemplate(
        keyword="срок",
        risk="Сжатые сроки исполнения",
        consequences="Риск срыва и санкций",
        mitigation="Согласовать реалистичный график",
    ),
    RiskTemplate(
        keyword="оплат",
        risk="Отсрочка платежа",
        consequences="Кассовый разрыв",
        mitigation="Уточнить график оплат и авансы",
    ),
    RiskTemplate(
        keyword="форс-мажор",
        risk="Неопределенный форс-мажор",
        consequences="Неясные условия освобождения от ответственности",
        mitigation="Уточнить перечень обстоятельств",
    ),
]


def _determine_row_count(text: str) -> int:
    base = max(5, math.ceil(len(text) / 400) + 4)
    return min(20, base)


def generate_risks_table(text: str) -> str:
    """Generate deterministic markdown risks table."""

    normalized_text = text.lower().strip()
    row_count = _determine_row_count(normalized_text)
    matched = [template for template in RISK_TEMPLATES if template.keyword in normalized_text]

    rows: list[tuple[str, str, str, str, str]] = []
    for template in matched:
        rows.append(
            (
                template.risk,
                template.consequences,
                "MEDIUM",
                "MEDIUM",
                template.mitigation,
            )
        )

    while len(rows) < row_count:
        rows.append(
            (
                "TBD",
                "Недостаточно данных",
                "TBD",
                "TBD",
                "ASSUMPTION: запросить недостающие условия",
            )
        )

    rows = rows[:row_count]

    table_lines = [
        "| № | Риск | Последствия | Вероятность | Влияние | Меры реагирования |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(rows, start=1):
        risk, consequences, probability, impact, mitigation = row
        table_lines.append(
            f"| {index} | {risk} | {consequences} | {probability} | {impact} | {mitigation} |"
        )

    missing_facts = []
    if len(matched) < 2:
        missing_facts.extend(
            [
                "сроки исполнения",
                "условия оплаты",
                "штрафы и ответственность",
                "порядок расторжения",
            ]
        )

    if missing_facts:
        table_lines.append("")
        table_lines.append("Недостаточно данных:")
        for item in missing_facts:
            table_lines.append(f"- {item}")

    return "\n".join(table_lines)
