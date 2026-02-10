"""Business logic for INN report pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.repositories import CompanyRepository
from src.integrations.dadata_client import dadata_client
from src.integrations.openai_best_effort import openai_best_effort_client
from src.services.risk_service import build_risk_assessment

logger = logging.getLogger(__name__)


@dataclass
class ReportResult:
    company_payload: dict
    affiliated_payload: dict | None
    risk_summary: str
    risk_flags: list[str]
    risk_score: float
    ai_summary: str | None


class ReportService:
    def __init__(self, session: AsyncSession):
        self.repo = CompanyRepository(session)

    async def get_or_build_report(self, tg_user_db_id: int, inn: str, update_id: int | None) -> ReportResult | None:
        cached = await self.repo.get_party_cache(inn)
        company = cached.payload if cached else None
        affiliated = cached.affiliated_payload if cached else None

        if not company:
            company = await dadata_client.find_party(inn)
            if not company:
                return None
            affiliated = await dadata_client.find_affiliated(inn)
            await self.repo.upsert_party_cache(inn, company, affiliated)

        data = company.get("data") or {}
        request = await self.repo.create_request(tg_user_db_id=tg_user_db_id, inn=inn, ogrn=data.get("ogrn"), update_id=update_id)

        score, flags, summary = build_risk_assessment(company)
        await self.repo.save_risk_assessment(request.id, score, flags, summary)

        ai_summary: str | None = None
        if settings.openai_api_key:
            ai_summary = await openai_best_effort_client.summarize(company_payload=company, risk_summary=summary)
            if ai_summary:
                await self.repo.save_ai_summary(request.id, ai_summary, settings.openai_model)

        return ReportResult(
            company_payload=company,
            affiliated_payload=affiliated,
            risk_summary=summary,
            risk_flags=flags,
            risk_score=score,
            ai_summary=ai_summary,
        )
