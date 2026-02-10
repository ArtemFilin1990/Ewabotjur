"""SQLAlchemy models for telegram bot state and company checks."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TgUser(Base):
    __tablename__ = "tg_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(64))
    last_inn: Mapped[str | None] = mapped_column(String(12))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ProcessedUpdate(Base):
    __tablename__ = "processed_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    update_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    tg_user_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), nullable=False)
    ogrn: Mapped[str | None] = mapped_column(String(15))
    update_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PartyCache(Base):
    __tablename__ = "party_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inn: Mapped[str] = mapped_column(String(12), nullable=False)
    ogrn: Mapped[str | None] = mapped_column(String(15))
    status: Mapped[str | None] = mapped_column(String(32))
    invalid: Mapped[bool | None] = mapped_column(Boolean)
    management: Mapped[dict | None] = mapped_column(JSONB)
    founders: Mapped[list | None] = mapped_column(JSONB)
    managers: Mapped[list | None] = mapped_column(JSONB)
    finance: Mapped[dict | None] = mapped_column(JSONB)
    licenses: Mapped[list | None] = mapped_column(JSONB)
    phones: Mapped[list | None] = mapped_column(JSONB)
    emails: Mapped[list | None] = mapped_column(JSONB)
    okveds: Mapped[list | None] = mapped_column(JSONB)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    affiliated_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("inn", name="uq_party_cache_inn"),)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    flags: Mapped[list] = mapped_column(JSONB, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AiSummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("ix_requests_created_at", Request.created_at)
Index("ix_requests_user_id", Request.tg_user_id)
