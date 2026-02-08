# Переменные окружения для Amvera Cloud

## Обязательные переменные

### База данных PostgreSQL
```
DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>:5432/<database>
```
**Примечание:** 
- Замените `<username>` и `<password>` на учетные данные пользователя БД
- Замените `<host>` на реальный хост базы данных, предоставленный Amvera
- Замените `<database>` на имя вашей базы данных

### Конфигурация приложения
```
PORT=3000
APP_URL=https://<your-domain>.amvera.ru
LOG_LEVEL=info
```

### Telegram Bot
```
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
TG_WEBHOOK_SECRET=<random-secret-string>
```
**Как получить:**
- Создайте бота через @BotFather в Telegram
- Скопируйте токен бота
- Для TG_WEBHOOK_SECRET используйте случайную строку (например, сгенерируйте через `openssl rand -hex 32`)

### DaData API
```
DADATA_API_KEY=<your-dadata-api-key>
DADATA_SECRET_KEY=<your-dadata-secret-key>
```
**Как получить:**
- Зарегистрируйтесь на https://dadata.ru
- Получите API ключи в личном кабинете

### OpenAI API (для GPT-анализа)
```
OPENAI_API_KEY=<your-openai-api-key>
```
**Как получить:**
- Зарегистрируйтесь на https://platform.openai.com
- Создайте API ключ в разделе API keys

### Bitrix24 OAuth
```
BITRIX_DOMAIN=<your-domain>.bitrix24.ru
BITRIX_CLIENT_ID=<your-client-id>
BITRIX_CLIENT_SECRET=<your-client-secret>
BITRIX_REDIRECT_URL=https://<your-domain>.amvera.ru/oauth/bitrix/callback
```
**Как получить:**
- Зайдите в настройки вашего Bitrix24
- Создайте локальное приложение (REST API)
- Скопируйте Client ID и Client Secret

## Опциональные переменные

### OpenAI Model Selection
```
OPENAI_MODEL=gpt-4
```
**Доступные модели:** gpt-4, gpt-4-turbo, gpt-3.5-turbo

### Feature Flags
```
ENABLE_TELEGRAM=true
ENABLE_BITRIX=true
ENABLE_DADATA=true
```

### MCP (Model Context Protocol) - Experimental
```
USE_MCP=false
MCP_SERVER_URL=<mcp-server-url>
MCP_API_KEY=<mcp-api-key>
```

## Пример полного набора переменных для Amvera

```bash
# === ОБЯЗАТЕЛЬНЫЕ ===
DATABASE_URL=postgresql+asyncpg://<username>:<password>@postgres.amvera.io:5432/<database>
PORT=3000
APP_URL=https://<your-domain>.amvera.ru
LOG_LEVEL=info

# Telegram
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
TG_WEBHOOK_SECRET=<use-openssl-rand-hex-32>

# DaData
DADATA_API_KEY=<your-dadata-api-key>
DADATA_SECRET_KEY=<your-dadata-secret-key>

# OpenAI
OPENAI_API_KEY=sk-proj-<your-openai-key>

# Bitrix24
BITRIX_DOMAIN=<your-company>.bitrix24.ru
BITRIX_CLIENT_ID=local.<your-client-id>
BITRIX_CLIENT_SECRET=<your-client-secret>
BITRIX_REDIRECT_URL=https://<your-domain>.amvera.ru/oauth/bitrix/callback

# === ОПЦИОНАЛЬНЫЕ ===
OPENAI_MODEL=gpt-4
ENABLE_TELEGRAM=true
ENABLE_BITRIX=true
ENABLE_DADATA=true
```

## Настройка в Amvera UI

1. Откройте панель управления проектом в Amvera
2. Перейдите в раздел "Переменные окружения" (Environment Variables)
3. Добавьте каждую переменную по одной:
   - Имя: `DATABASE_URL`
   - Значение: `postgresql+asyncpg://...`
   - Нажмите "Добавить"
4. Повторите для всех переменных из списка
5. Сохраните изменения
6. Перезапустите приложение

## После развертывания

### Настройка Telegram Webhook

После успешного деплоя выполните следующую команду для установки webhook:

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<your-domain>.amvera.ru/webhook/telegram/<TG_WEBHOOK_SECRET>",
    "secret_token": "<TG_WEBHOOK_SECRET>"
  }'
```

Проверка статуса webhook:
```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

### Первичная авторизация Bitrix24

1. Откройте в браузере: `https://<your-domain>.amvera.ru/oauth/bitrix`
2. Разрешите доступ приложению
3. Токены будут автоматически сохранены в базе данных PostgreSQL

## Проверка работоспособности

1. Health check: `curl https://<your-domain>.amvera.ru/health`
   - Ожидаемый ответ: `{"status": "ok"}`

2. Отправьте ИНН боту в Telegram (например: `7707083893`)
   - Бот должен ответить с информацией о компании

3. Проверьте логи в Amvera UI для диагностики проблем

## Безопасность

⚠️ **ВАЖНО:**
- Никогда не коммитьте файлы с реальными значениями переменных в Git
- Используйте только `.env.example` как шаблон
- Храните секреты только в Amvera UI или защищенных системах управления секретами
- Регулярно ротируйте API ключи
- Используйте сильные случайные значения для TG_WEBHOOK_SECRET

## Troubleshooting

### База данных не подключается
- Проверьте формат `DATABASE_URL` (должен быть `postgresql+asyncpg://`)
- Убедитесь, что PostgreSQL доступна из Amvera
- Проверьте правильность учетных данных

### Telegram webhook не работает
- Проверьте, что URL доступен извне
- Убедитесь, что TG_WEBHOOK_SECRET совпадает в URL и в переменных
- Проверьте логи приложения

### Bitrix24 OAuth не проходит
- Проверьте, что BITRIX_REDIRECT_URL точно совпадает с настройками в Bitrix24
- Убедитесь, что приложение активно в Bitrix24
- Проверьте Client ID и Client Secret
