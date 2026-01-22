import requests
from app.config import DADATA_TOKEN, DADATA_SECRET

DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"

async def dadata_find_by_inn(inn: str) -> dict | None:
    if not DADATA_TOKEN:
        return None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {DADATA_TOKEN}",
    }
    if DADATA_SECRET:
        headers["X-Secret"] = DADATA_SECRET

    payload = {"query": inn}

    # requests синхронный, но для старта ок; потом заменим на httpx/async.
    r = requests.post(DADATA_URL, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    j = r.json()
    suggestions = j.get("suggestions", [])
    return suggestions[0] if suggestions else None
