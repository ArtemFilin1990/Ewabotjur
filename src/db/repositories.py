"""Repository layer for DB access."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AiSummary, PartyCache, ProcessedUpdate, Request, RiskAssessment, TgUser


class TelegramRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def mark_update_processed(self, update_id: int, tg_user_id: int | None) -> bool:
        existing = await self.session.scalar(select(ProcessedUpdate).where(ProcessedUpdate.update_id == update_id))
        if existing:
            return False
        self.session.add(ProcessedUpdate(update_id=update_id, tg_user_id=tg_user_id))
        await self.session.commit()
        return True

    async def upsert_user(self, tg_user_id: int, username: str | None, first_name: str | None, last_name: str | None) -> TgUser:
        user = await self.session.scalar(select(TgUser).where(TgUser.tg_user_id == tg_user_id))
        if not user:
            user = TgUser(tg_user_id=tg_user_id, username=username, first_name=first_name, last_name=last_name)
            self.session.add(user)
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_user_state(self, user: TgUser, state: str | None) -> None:
        user.state = state
        await self.session.commit()

    async def set_last_inn(self, user: TgUser, inn: str) -> None:
        user.last_inn = inn
        await self.session.commit()


class CompanyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_party_cache(self, inn: str) -> PartyCache | None:
        return await self.session.scalar(select(PartyCache).where(PartyCache.inn == inn))

    async def upsert_party_cache(self, inn: str, party_data: dict[str, Any], affiliated_data: dict[str, Any] | None) -> PartyCache:
        cache = await self.get_party_cache(inn)
        parsed = party_data.get("data", {})
        status = (parsed.get("state") or {}).get("status")
        if not cache:
            cache = PartyCache(
                inn=inn,
                ogrn=parsed.get("ogrn"),
                status=status,
                invalid=bool(parsed.get("invalid")),
                management=parsed.get("management"),
                founders=parsed.get("founders") or [],
                managers=parsed.get("managers") or [],
                finance=parsed.get("finance"),
                licenses=parsed.get("licenses") or [],
                phones=parsed.get("phones") or [],
                emails=parsed.get("emails") or [],
                okveds=parsed.get("okveds") or [],
                payload=party_data,
                affiliated_payload=affiliated_data,
            )
            self.session.add(cache)
        else:
            cache.ogrn = parsed.get("ogrn")
            cache.status = status
            cache.invalid = bool(parsed.get("invalid"))
            cache.management = parsed.get("management")
            cache.founders = parsed.get("founders") or []
            cache.managers = parsed.get("managers") or []
            cache.finance = parsed.get("finance")
            cache.licenses = parsed.get("licenses") or []
            cache.phones = parsed.get("phones") or []
            cache.emails = parsed.get("emails") or []
            cache.okveds = parsed.get("okveds") or []
            cache.payload = party_data
            cache.affiliated_payload = affiliated_data
        await self.session.commit()
        await self.session.refresh(cache)
        return cache

    async def create_request(self, tg_user_db_id: int, inn: str, ogrn: str | None, update_id: int | None) -> Request:
        request = Request(tg_user_id=tg_user_db_id, inn=inn, ogrn=ogrn, update_id=update_id)
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def save_risk_assessment(self, request_id: int, risk_score: float, flags: list[str], summary: str) -> RiskAssessment:
        risk = RiskAssessment(request_id=request_id, risk_score=risk_score, flags=flags, summary=summary)
        self.session.add(risk)
        await self.session.commit()
        await self.session.refresh(risk)
        return risk

    async def save_ai_summary(self, request_id: int, summary: str, model: str) -> AiSummary:
        ai = AiSummary(request_id=request_id, summary=summary, model=model)
        self.session.add(ai)
        await self.session.commit()
        await self.session.refresh(ai)
        return ai
