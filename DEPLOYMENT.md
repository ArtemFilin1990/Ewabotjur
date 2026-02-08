# Деплой на Amvera (FastAPI + PostgreSQL)

## Предварительные требования
1. Аккаунт на [Amvera](https://amvera.ru)
2. GitHub репозиторий приложения
3. PostgreSQL база данных (для хранения токенов Bitrix24)
4. Подготовленные API ключи

## Шаг 1: Деплой приложения
1. Войдите в [Amvera Console](https://console.amvera.ru)
2. Создайте приложение из GitHub
3. Убедитесь, что используется конфигурация `amvera.yml` с Python-окружением
4. Запустите деплой

## Шаг 2: Переменные окружения
Добавьте переменные в UI Amvera:
```env
TELEGRAM_BOT_TOKEN=<ваш токен от BotFather>
TG_WEBHOOK_SECRET=<случайная строка>
DADATA_API_KEY=<ваш API ключ DaData>
DADATA_SECRET_KEY=<ваш секретный ключ DaData>
OPENAI_API_KEY=<ваш ключ OpenAI>
BITRIX_DOMAIN=https://вашкомпания.bitrix24.ru
BITRIX_CLIENT_ID=<Client ID из Bitrix24>
BITRIX_CLIENT_SECRET=<Client Secret из Bitrix24>
BITRIX_REDIRECT_URL=https://<ваш_домен>/oauth/bitrix/callback
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname

# Опциональные
APP_URL=https://<ваш_домен>
LOG_LEVEL=INFO
OPENAI_MODEL=gpt-4
```

## Шаг 3: Настройка Telegram Webhook
```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<ваш_домен>/webhook/telegram/<TG_WEBHOOK_SECRET>"
  }'
```

Проверка webhook:
```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

## Шаг 4: Настройка Bitrix24 OAuth
1. В Bitrix24 укажите Redirect URI: `https://<ваш_домен>/oauth/bitrix/callback`
2. После деплоя откройте `https://<ваш_домен>/oauth/bitrix` и завершите авторизацию
3. Токены сохраняются в PostgreSQL (таблица `bitrix_tokens`)

## Проверка работы
Health check:
```bash
curl https://<ваш_домен>/health
```

Ожидаемый ответ:
```json
{"status":"ok"}
```
