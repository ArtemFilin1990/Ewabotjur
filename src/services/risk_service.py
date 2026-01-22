"""Risk analysis service for contract text."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class RiskTable:
    """Risk table output."""

    markdown: str
    missing_data: list[str]


class RiskAnalysisService:
    """Generate a deterministic risk table based on missing clauses."""

    MIN_TEXT_LENGTH = 200

    SECTION_RULES: dict[str, Iterable[str]] = {
        "условие о предмете договора": ("предмет", "оказание услуг", "поставка", "работ"),
        "условие о цене/оплате": ("оплата", "цена", "стоимость", "вознаграждени"),
        "условие о сроках исполнения": ("срок", "период", "дата исполнения"),
        "условие об ответственности": ("ответствен", "штраф", "пеня", "неустойк"),
        "условие о расторжении": ("расторж", "односторонн", "прекращени"),
        "условие о форс-мажоре": ("форс-мажор", "обстоятельств непреодолимой силы"),
    }

    def generate_risk_table(self, text: str) -> RiskTable:
        """Generate markdown risk table."""

        normalized = self._normalize(text)
        if len(normalized) < self.MIN_TEXT_LENGTH:
            return RiskTable(
                markdown=self._build_table([
                    (
                        "TBD: Недостаточно текста для анализа",
                        "Требуется полный текст договора",
                        "Неизвестно",
                        "Неизвестно",
                        "Предоставьте полный текст договора",
                    )
                ]),
                missing_data=["Полный текст договора или ключевые разделы"],
            )

        rows = []
        missing_sections = []
        for section, keywords in self.SECTION_RULES.items():
            if not self._contains_any(normalized, keywords):
                missing_sections.append(section)
                rows.append(
                    (
                        f"Отсутствует {section}",
                        "Риск споров из-за неопределённости условий",
                        "Средняя",
                        "Среднее",
                        f"Добавить {section} в договор",
                    )
                )

        if not rows:
            rows.append(
                (
                    "Критичных пробелов по ключевым разделам не выявлено",
                    "Низкий риск по структуре условий",
                    "Низкая",
                    "Низкое",
                    "Провести детальную юридическую проверку условий",
                )
            )

        return RiskTable(markdown=self._build_table(rows), missing_data=missing_sections)

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    @staticmethod
    def _contains_any(text: str, keywords: Iterable[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _build_table(rows: list[tuple[str, str, str, str, str]]) -> str:
        header = "| № | Риск | Последствия | Вероятность | Влияние | Меры реагирования |"
        divider = "|---|------|-------------|-------------|---------|-------------------|"
        lines = [header, divider]
        for index, row in enumerate(rows, start=1):
            lines.append(
                f"| {index} | {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |"
            )
        return "\n".join(lines)
