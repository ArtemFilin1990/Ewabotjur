"""Inline keyboards for telegram UX."""


def main_menu() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "✅ Проверить ИНН", "callback_data": "menu:check_inn"}],
            [{"text": "🧾 Полная карточка (DaData)", "callback_data": "menu:card"}],
            [{"text": "🧩 Аффилированные", "callback_data": "menu:affiliated"}],
            [{"text": "⚠️ Риски", "callback_data": "menu:risks"}],
            [{"text": "📞 Контакты", "callback_data": "menu:contacts"}],
            [{"text": "ℹ️ Помощь / как пользоваться", "callback_data": "menu:help"}],
        ]
    }
