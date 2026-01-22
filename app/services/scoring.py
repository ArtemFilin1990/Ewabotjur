def score_company(suggestion: dict) -> str:
    data = suggestion.get("data", {})
    name = suggestion.get("value", "—")
    state = (data.get("state") or {}).get("status", "—")
    inn = data.get("inn", "—")
    ogrn = data.get("ogrn", "—")
    address = ((data.get("address") or {}).get("value")) or "—"
    director = ((data.get("management") or {}).get("name")) or "—"

    risk_flags = []
    if state != "ACTIVE":
        risk_flags.append("статус не ACTIVE")
    if (data.get("address") or {}).get("qc") == "1":
        risk_flags.append("адрес требует уточнения")

    if risk_flags:
        level = "ВЫСОКИЙ"
    else:
        level = "НИЗКИЙ"

    reasons = ", ".join(risk_flags) if risk_flags else "явных флагов не найдено"

    return (
        f"Компания: {name}\n"
        f"ИНН: {inn}\n"
        f"ОГРН: {ogrn}\n"
        f"Директор: {director}\n"
        f"Адрес: {address}\n"
        f"Статус: {state}\n\n"
        f"Скоринг: {level}\n"
        f"Причины: {reasons}"
    )
