"""User-facing message templates."""

from __future__ import annotations


HELP_TEXT = (
    "Команды бота:\n"
    "/start — краткая справка\n"
    "/help — список команд\n"
    "/ping — проверка связи\n"
    "/company_check <ИНН> — карточка контрагента + риск\n"
    "/risks [--docx|--md] — таблица рисков по тексту договора\n"
    "/clear_memory — очистить память чата\n"
    "/new_task — сбросить текущую задачу\n\n"
    "Поддерживаемые файлы: PDF, DOCX, TXT (до 15 МБ)."
)


START_TEXT = (
    "Юрист-бот готов к работе.\n"
    "Отправьте /help, чтобы увидеть список доступных команд."
)


ACCESS_DENIED_TEXT = "⛔ Доступ запрещён. Обратитесь к администратору."
