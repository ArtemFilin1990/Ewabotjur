"""Response renderers for bot commands."""

from __future__ import annotations

from app.services.dadata import CompanyProfile
from app.services.scoring import ScoreResult


def render_company_response(profile: CompanyProfile, score: ScoreResult) -> str:
    """Render company card + score summary."""

    lines = ["Компания:"]
    lines.append(f"- Наименование: {profile.name or 'TBD'}")
    lines.append(f"- ИНН: {profile.inn or 'TBD'}")
    lines.append(f"- ОГРН: {profile.ogrn or 'TBD'}")
    lines.append(f"- КПП: {profile.kpp or 'TBD'}")
    lines.append(f"- Адрес: {profile.address or 'TBD'}")
    lines.append(f"- Руководитель: {profile.director or 'TBD'}")
    lines.append(f"- Статус: {profile.status or 'TBD'}")
    lines.append(f"- Дата регистрации: {profile.registration_date or 'TBD'}")

    lines.append("")
    lines.append("Скоринг:")
    lines.append(f"- Уровень риска: {score.risk_level}")
    lines.append("- Причины:")
    for reason in score.reasons:
        lines.append(f"  - {reason}")

    return "\n".join(lines)
