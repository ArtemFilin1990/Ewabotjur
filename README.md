# Ewabotjur

Telegram + Bitrix24 бот для анализа контрагентов по ИНН с использованием DaData и GPT.

## 🎯 Возможности

- ✅ Получение данных о компаниях по ИНН через DaData API
- ✅ Анализ рисков и рекомендации через OpenAI GPT
- ✅ Интеграция с Telegram (webhook)
- ✅ Интеграция с Bitrix24 imbot (OAuth 2.0 с auto-refresh)
- ✅ Готовый к деплою на Amvera

## 🏗️ Архитектура

```
┌─────────────┐       ┌──────────────┐
│  Telegram   │──────▶│   FastAPI    │
│   Webhook   │       │  Application │
└─────────────┘       └──────┬───────┘
                             │
┌─────────────┐              │
│  Bitrix24   │──────────────┤
│   Webhook   │              │
└─────────────┘              │
                             │
                    ┌────────▼────────┐
                    │   INN Parser    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  DaData API     │
                    │  (Company Info) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   OpenAI GPT    │
                    │   (Analysis)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Response to    │
                    │ Telegram/Bitrix │
                    └─────────────────┘
```

## 📋 Требования

- Python 3.11+
- Docker (для деплоя)
- API ключи:
  - Telegram Bot Token
  - DaData API Key
  - OpenAI API Key
  - Bitrix24 OAuth credentials

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/ArtemFilin1990/Ewabotjur.git
cd Ewabotjur
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
# Заполните .env реальными значениями
```

### 3. Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
python -m src.main
```

Приложение будет доступно на `http://localhost:3000`

### 4. Установка Telegram webhook

```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=https://<YOUR_DOMAIN>/webhook/telegram/<TG_WEBHOOK_SECRET>"
```

## 🐳 Деплой на Amvera

### Шаг 1: Подготовка репозитория

Файлы для Amvera уже готовы:
- `Dockerfile` — многоэтапная сборка Python приложения
- `amvera.yml` — конфигурация с containerPort: 3000

### Шаг 2: Создание приложения в Amvera

1. Перейдите в UI Amvera
2. Create application
3. Source: GitHub
4. Repo: `ArtemFilin1990/Ewabotjur`
5. Branch: `main`
6. Toolchain: Docker
7. Deploy

### Шаг 3: Настройка переменных окружения

В разделе "Переменные" Amvera добавьте:

**Обязательные:**
- `TELEGRAM_BOT_TOKEN` — токен от @BotFather
- `TG_WEBHOOK_SECRET` — случайная строка для безопасности
- `DADATA_API_KEY` — ключ DaData
- `DADATA_SECRET_KEY` — секретный ключ DaData
- `OPENAI_API_KEY` — ключ OpenAI
- `BITRIX_DOMAIN` — домен Bitrix24 (https://xxx.bitrix24.ru)
- `BITRIX_CLIENT_ID` — Client ID приложения Bitrix24
- `BITRIX_CLIENT_SECRET` — Client Secret приложения Bitrix24
- `BITRIX_REDIRECT_URL` — URL callback (https://your-app.amvera.app/oauth/bitrix/callback)

**Опциональные:**
- `APP_URL` — URL вашего приложения на Amvera
- `LOG_LEVEL` — уровень логирования (INFO, DEBUG, WARNING, ERROR)
- `OPENAI_MODEL` — модель GPT (по умолчанию gpt-4)
- `USE_MCP` — использовать MCP (true/false)
- `MCP_SERVER_URL` — URL MCP сервера
- `MCP_API_KEY` — ключ MCP

После изменения переменных перезапустите контейнер.

### Шаг 4: Установка webhook

После деплоя у вас будет URL: `https://<app>.amvera.app`

Установите Telegram webhook:

```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=https://<app>.amvera.app/webhook/telegram/<TG_WEBHOOK_SECRET>"
```

### Шаг 5: Настройка Bitrix24 OAuth

1. В Bitrix24 создайте приложение типа "Локальное приложение"
2. Укажите redirect URL: `https://<app>.amvera.app/oauth/bitrix/callback`
3. Получите Client ID и Client Secret
4. Добавьте их в переменные окружения Amvera
5. Перейдите по адресу: `https://<app>.amvera.app/oauth/bitrix/start`
6. Пройдите авторизацию
7. Токены сохранятся в `storage/bitrix_tokens.json`

## 📖 API Endpoints

### Health Check
```
GET /health
```

Ответ:
```json
{
  "status": "healthy",
  "has_telegram_token": true,
  "has_dadata_key": true,
  "has_openai_key": true,
  "has_bitrix_config": true
}
```

### Telegram Webhook
```
POST /webhook/telegram/{secret}
```

Принимает update от Telegram.

### Bitrix24 Webhook
```
POST /webhook/bitrix
```

Принимает события от Bitrix24 imbot.

### Bitrix24 OAuth

**Инициация:**
```
GET /oauth/bitrix/start
```

**Callback:**
```
GET /oauth/bitrix/callback?code=...
```

## 🧪 Тестирование

```bash
# Запуск тестов
python -m unittest discover tests

# Конкретный тест
python -m unittest tests.test_inn_parser
```

## 📝 Логирование

Приложение использует структурированное логирование:
- Уровень задаётся через `LOG_LEVEL`
- Логи не содержат токены и секреты (только `has_token: true/false`)
- Формат: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## 🔒 Безопасность

- ❌ Никогда не коммитьте секреты в репозиторий
- ✅ Все секреты через переменные окружения
- ✅ Webhook Telegram защищён секретным ключом
- ✅ Bitrix24 OAuth с refresh token
- ✅ Логи не содержат чувствительных данных

## 🤖 Принципы работы с GPT

**Важно:** GPT формирует ТОЛЬКО выводы и рекомендации. Все факты берутся ТОЛЬКО из DaData.

GPT НЕ должен:
- ❌ Придумывать финансовые показатели
- ❌ Делать выводы о том, о чём нет данных
- ❌ Давать юридические заключения

GPT должен:
- ✅ Анализировать имеющиеся данные
- ✅ Выявлять риски на основе фактов
- ✅ Рекомендовать документы для запроса
- ✅ Давать практические советы

Системный промпт находится в `prompts/inn_score.md`.

## 🛠️ Структура проекта

```
Ewabotjur/
├── Dockerfile              # Docker образ для Amvera
├── amvera.yml             # Конфигурация Amvera
├── requirements.txt       # Python зависимости
├── .env.example          # Пример переменных окружения
├── README.md             # Документация
├── src/
│   ├── main.py          # Точка входа FastAPI
│   ├── config.py        # Конфигурация из env
│   ├── integrations/    # Интеграции с внешними API
│   │   ├── telegram.py
│   │   ├── dadata.py
│   │   ├── openai_client.py
│   │   └── bitrix24/
│   │       ├── oauth.py    # OAuth 2.0 с auto-refresh
│   │       └── api.py      # Bitrix24 REST API
│   ├── handlers/        # Обработчики событий
│   │   ├── telegram_handler.py
│   │   └── bitrix_handler.py
│   └── utils/          # Утилиты
│       └── inn_parser.py   # Парсинг ИНН
├── prompts/
│   └── inn_score.md    # Системный промпт для GPT
└── tests/              # Тесты
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи приложения
2. Убедитесь, что все переменные окружения установлены
3. Проверьте валидность API ключей
4. Убедитесь, что webhook установлен правильно

## 📄 Лицензия

MIT License

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) — веб-фреймворк
- [DaData](https://dadata.ru/) — данные о компаниях
- [OpenAI](https://openai.com/) — GPT для анализа
- [Telegram Bot API](https://core.telegram.org/bots/api) — Telegram интеграция
- [Bitrix24](https://dev.bitrix24.ru/) — Bitrix24 REST API
