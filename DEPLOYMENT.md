# Быстрый старт: Деплой на Amvera

## Предварительные требования

1. Аккаунт на [Amvera](https://amvera.ru)
2. GitHub репозиторий: `ArtemFilin1990/Ewabotjur`
3. Подготовленные API ключи (см. ниже)

## Шаг 1: Получение API ключей

### Telegram Bot Token
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен (например: `1234567890:ABCdefGhIjklMnoPQRstuVWXyz`)

### DaData API
1. Зарегистрируйтесь на [dadata.ru](https://dadata.ru)
2. Перейдите в "Профиль" → "API ключи"
3. Скопируйте API ключ и секретный ключ

### OpenAI API
1. Зарегистрируйтесь на [platform.openai.com](https://platform.openai.com)
2. Перейдите в "API Keys"
3. Создайте новый ключ
4. Скопируйте ключ (начинается с `sk-`)

### Bitrix24
1. Войдите в свой Bitrix24 портал
2. Перейдите в "Приложения" → "Создать приложение"
3. Выберите "Локальное приложение"
4. Укажите название и права доступа (нужен `imbot`)
5. Скопируйте Client ID и Client Secret
6. Укажите Redirect URI (будет известен после деплоя)

## Шаг 2: Деплой на Amvera

### 2.1 Создание приложения

1. Войдите в [Amvera Console](https://console.amvera.ru)
2. Нажмите **"Create Application"**
3. Выберите **"From GitHub"**
4. Выберите репозиторий: `ArtemFilin1990/Ewabotjur`
5. Ветка: `main`
6. Toolchain: **Node.js (npm)** (без Dockerfile)
7. Нажмите **"Deploy"**

> Примечание: для режима node + npm не используйте `Dockerfile` и `requirements.txt` — они не нужны и только раздувают архив деплоя.

### 2.2 Настройка переменных окружения

После создания приложения, перейдите в раздел **"Переменные"**:

```env
# Обязательные переменные
TELEGRAM_BOT_TOKEN=<ваш токен от BotFather>
TG_WEBHOOK_SECRET=<случайная строка, например: mySecretKey123>
DADATA_API_KEY=<ваш API ключ DaData>
DADATA_SECRET_KEY=<ваш секретный ключ DaData>
OPENAI_API_KEY=<ваш ключ OpenAI>
BITRIX_DOMAIN=https://вашкомпания.bitrix24.ru
BITRIX_CLIENT_ID=<Client ID из Bitrix24>
BITRIX_CLIENT_SECRET=<Client Secret из Bitrix24>
BITRIX_REDIRECT_URL=https://your-app.amvera.app/oauth/bitrix/callback

# Опциональные
APP_URL=https://your-app.amvera.app
LOG_LEVEL=INFO
OPENAI_MODEL=gpt-4
```

**ВАЖНО:** Замените `your-app` на реальное имя вашего приложения в Amvera.

### 2.3 Перезапуск после настройки переменных

После добавления переменных:
1. Нажмите **"Save"**
2. Нажмите **"Restart"** для применения изменений

## Шаг 3: Настройка Telegram Webhook

После успешного деплоя, ваше приложение доступно по адресу:
```
https://your-app.amvera.app
```

Установите webhook для Telegram:

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.amvera.app/webhook/telegram/<TG_WEBHOOK_SECRET>"
  }'
```

Замените:
- `<TELEGRAM_BOT_TOKEN>` на ваш токен
- `your-app` на имя вашего приложения
- `<TG_WEBHOOK_SECRET>` на значение из переменных окружения

Проверка webhook:
```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

## Шаг 4: Настройка Bitrix24 OAuth

### 4.1 Обновление Redirect URL в Bitrix24

1. Вернитесь в настройки приложения в Bitrix24
2. Укажите Redirect URI: `https://your-app.amvera.app/oauth/bitrix/callback`
3. Сохраните

### 4.2 Авторизация бота

**ВАЖНО о хранении токенов:**
- Токены Bitrix24 хранятся в файле `storage/bitrix_tokens.json`
- В контейнере Docker токены будут теряться при перезапуске
- Для продакшена рекомендуется:
  - Настроить persistent volume в Amvera для директории `/app/storage`
  - Или использовать внешнее хранилище (PostgreSQL, Redis)
  - Или повторно проходить OAuth после каждого деплоя

**Авторизация:**

1. Откройте в браузере: `https://your-app.amvera.app/oauth/bitrix`
2. Вы будете перенаправлены на страницу авторизации Bitrix24
3. Разрешите доступ приложению
4. После успешной авторизации вы увидите сообщение об успехе
5. Токены сохранятся в `storage/bitrix_tokens.json`

**Примечание:** Если после рестарта бот перестал работать с Bitrix24, повторите авторизацию.

## Шаг 5: Проверка работы

### Telegram Bot

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Отправьте ИНН компании (например: `7707083893`)
4. Получите анализ

### Bitrix24 Bot

1. Откройте чат с ботом в Bitrix24
2. Отправьте ИНН компании
3. Получите анализ

### Health Check

Проверьте статус приложения:
```bash
curl https://your-app.amvera.app/health
```

Ответ должен быть:
```json
{
  "status": "healthy",
  "has_telegram_token": true,
  "has_dadata_key": true,
  "has_openai_key": true,
  "has_bitrix_config": true
}
```

## Troubleshooting

### Проблема: Бот не отвечает в Telegram

**Решение:**
1. Проверьте что webhook установлен: `/getWebhookInfo`
2. Проверьте логи в Amvera Console
3. Убедитесь что `TG_WEBHOOK_SECRET` совпадает в переменных и URL

### Проблема: "Missing environment variables"

**Решение:**
1. Проверьте что все переменные добавлены в Amvera
2. Перезапустите приложение после добавления переменных
3. Проверьте `/health` endpoint

### Проблема: OAuth ошибка в Bitrix24

**Решение:**
1. Убедитесь что Redirect URL правильный
2. Проверьте что Client ID и Secret верны
3. Попробуйте заново `/oauth/bitrix`

### Проблема: "DaData API error"

**Решение:**
1. Проверьте лимиты на тарифе DaData
2. Убедитесь что ключи правильные
3. Проверьте что ИНН корректный

## Мониторинг

### Логи приложения

В Amvera Console:
1. Перейдите в раздел **"Logs"**
2. Выберите уровень логирования
3. Наблюдайте за работой приложения

### Метрики

Следите за:
- Использование CPU
- Использование памяти
- Количество запросов
- Время ответа

## Обновление приложения

При обновлении кода в GitHub:
1. Amvera автоматически пересобирает приложение
2. Или используйте ручной **"Redeploy"** в консоли
3. Проверьте логи после обновления

## Безопасность

✅ **ВСЕГДА:**
- Используйте HTTPS (Amvera обеспечивает автоматически)
- Храните секреты в переменных окружения
- Регулярно обновляйте зависимости
- Следите за логами на предмет подозрительной активности

❌ **НИКОГДА:**
- Не коммитьте `.env` файл
- Не публикуйте API ключи
- Не отключайте webhook secret

## Полезные ссылки

- [Документация Amvera](https://docs.amvera.ru/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [DaData API](https://dadata.ru/api/)
- [OpenAI API](https://platform.openai.com/docs)
- [Bitrix24 REST API](https://dev.bitrix24.ru/)

## Поддержка

При возникновении вопросов:
1. Проверьте логи в Amvera Console
2. Изучите документацию
3. Откройте issue в GitHub репозитории
