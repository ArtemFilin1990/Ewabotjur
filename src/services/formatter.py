"""Telegram response formatting."""
from __future__ import annotations

from typing import Any


def _safe_join(items: list[Any] | None, fallback: str = "нет данных") -> str:
    if not items:
        return fallback
    return ", ".join(str(item) for item in items[:15])


def format_party_card(company: dict[str, Any]) -> str:
    data = company.get("data") or {}
    state = data.get("state") or {}
    name = (data.get("name") or {}).get("full_with_opf") or (data.get("name") or {}).get("full") or "—"
    management = data.get("management") or {}
    return (
        "🧾 Полная карточка (DaData)\n"
        f"Наименование: {name}\n"
        f"ИНН: {data.get('inn', '—')}\n"
        f"ОГРН: {data.get('ogrn', '—')}\n"
        f"Статус: {state.get('status', '—')}\n"
        f"Руководитель: {management.get('name', '—')}\n"
        f"Телефоны: {_safe_join(data.get('phones'))}\n"
        f"Emails: {_safe_join(data.get('emails'))}"
    )


def format_affiliated(affiliated: dict[str, Any] | None) -> str:
    if not affiliated:
        return "🧩 Аффилированные: данные временно недоступны."
    suggestions = affiliated.get("suggestions") or []
    if not suggestions:
        return "🧩 Аффилированные: не найдено."
    lines = ["🧩 Аффилированные:"]
    for item in suggestions[:10]:
        data = item.get("data") or {}
        n = (data.get("name") or {}).get("short_with_opf") or item.get("value")
        lines.append(f"• {n} (ИНН {data.get('inn', '—')})")
    return "\n".join(lines)


def format_help() -> str:
    return (
        "ℹ️ Как пользоваться:\n"
        "1) Нажмите «Проверить ИНН».\n"
        "2) Отправьте ИНН 10/12 цифр.\n"
        "3) Получите карточку, риски и аффилированных."
    )


def split_telegram_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            parts.append(rest)
            break
        idx = rest.rfind("\n", 0, limit)
        if idx == -1:
            idx = limit
        parts.append(rest[:idx])
        rest = rest[idx:].lstrip()
    return parts
