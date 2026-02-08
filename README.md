# Ewabotjur (FastAPI)

Telegram + Bitrix24 бот для анализа контрагентов по ИНН с использованием DaData и OpenAI.

## Требования
- Python 3.11+
- PostgreSQL (для хранения OAuth токенов Bitrix24)

## Переменные окружения
Обязательные:
- `PORT` (по умолчанию 3000)
- `APP_URL`
- `LOG_LEVEL`
- `TELEGRAM_BOT_TOKEN`
- `TG_WEBHOOK_SECRET` (или `TELEGRAM_WEBHOOK_SECRET`)
- `DADATA_API_KEY`
- `DADATA_SECRET_KEY`
- `OPENAI_API_KEY`
- `BITRIX_DOMAIN`
- `BITRIX_CLIENT_ID`
- `BITRIX_CLIENT_SECRET`
- `BITRIX_REDIRECT_URL`
- `DATABASE_URL` (формат: `postgresql+asyncpg://user:pass@host:port/dbname`)

Опциональные:
- `OPENAI_MODEL`
- `USE_MCP`
- `MCP_SERVER_URL`
- `MCP_API_KEY`

## Установка и запуск

### Локальная разработка
```bash
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
python -m uvicorn src.main:app --host 0.0.0.0 --port 3000
```

> **Важно для Amvera:** На платформе Amvera виртуальное окружение создается автоматически. **НЕ** добавляйте команды активации venv в cron задачи или скрипты на Amvera. См. [AMVERA_CRON_FIX.md](./AMVERA_CRON_FIX.md) для деталей.

## Эндпоинты
- `GET /` — базовый статус
- `GET /health` — health check
- `POST /webhook/telegram/{secret}` — webhook для Telegram
- `POST /bitrix/event` — события Bitrix24
- `GET /oauth/bitrix` — старт OAuth Bitrix24
- `GET /oauth/bitrix/callback` — callback OAuth Bitrix24

## Деплой на Amvera
1. Укажите `amvera.yml` с Python-окружением.
2. Добавьте переменные окружения в UI Amvera.
3. Убедитесь, что доступна PostgreSQL и задан `DATABASE_URL`.
4. После деплоя откройте `https://<your-app>.amvera.io/oauth/bitrix` для первичной авторизации.

## Настройка Telegram webhook
```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=https://<your-app>.amvera.io/webhook/telegram/<TG_WEBHOOK_SECRET>"
```

Проверка статуса webhook:
```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

## Тесты
```bash
pytest -q
```

## Troubleshooting

### Ошибка: "bash: line 1: /app/venv/bin/activate: No such file or directory"
Эта ошибка возникает при неправильной настройке cron задач на Amvera. См. подробное руководство: [AMVERA_CRON_FIX.md](./AMVERA_CRON_FIX.md)

### Другие проблемы
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Инструкции по деплою
- [AMVERA_ENV_VARS.md](./AMVERA_ENV_VARS.md) - Настройка переменных окружения
- [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) - Production чеклист
