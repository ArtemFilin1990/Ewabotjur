# Ewabotjur - Telegram Jurist Bot

Production-ready Telegram bot with Vercel webhook + Render worker architecture.

## ✅ Capabilities

- `/ping` → `pong`
- `/company_check <ИНН>` → карточка DaData + базовый риск
- `/risks` → таблица рисков по тексту или файлу
- Поддержка файлов PDF/DOCX/TXT
- Контроль доступа через `ALLOWED_CHAT_IDS`
- Vercel webhook мгновенно ACK, вся логика на Render worker

## 🧭 Архитектура

```
Vercel (Next.js) -> POST /api/telegram -> Render worker POST /ingest
```

Render worker выполняет:
- парсинг команд
- работу с DaData
- скачивание файлов из Telegram
- извлечение текста
- генерацию ответа и файлов

## ⚙️ Environment variables

### Vercel (Webhook)

- `RENDER_WORKER_URL` — URL Render сервиса (пример: `https://jurist-worker.onrender.com`)
- `WORKER_AUTH_TOKEN` — токен для аутентификации worker
- `TELEGRAM_WEBHOOK_SECRET` — опциональный секрет для заголовка `X-TG-SECRET`

### Render (Worker)

- `TELEGRAM_BOT_TOKEN` — токен Telegram Bot API
- `WORKER_AUTH_TOKEN` — токен для проверки `Authorization: Bearer ...`
- `ALLOWED_CHAT_IDS` — разрешённые chat_id через запятую
- `DADATA_TOKEN` — токен DaData
- `DADATA_SECRET` — опциональный секрет DaData
- `HTTP_TIMEOUT_SECONDS` — таймаут внешних вызовов
- `MAX_FILE_SIZE_MB` — лимит файлов (по умолчанию 15)
- `MEMORY_STORE_PATH` — путь к JSON-памяти
- `LOG_LEVEL` — уровень логирования

Полный список переменных доступен в `.env.example`.

## 🔐 Telegram webhook setup

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<your-vercel-app>/api/telegram",
    "secret_token": "<TELEGRAM_WEBHOOK_SECRET>"
  }'
```

Проверка:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

## 🧪 Локальный запуск (Render worker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=...
export WORKER_AUTH_TOKEN=...
export ALLOWED_CHAT_IDS=...
export DADATA_TOKEN=...
python -m src.worker_main
```

## 🧾 Команды бота

- `/start` — справка
- `/help` — справка
- `/ping` — pong
- `/company_check <ИНН>` — карточка контрагента + риск
- `/risks [текст] [--file]` — таблица рисков (флаг `--file` выдаст Markdown файл)
- `/clear_memory` — очистить память
- `/new_task` — сбросить контекст задачи

## 🧷 Render setup (manual)

1. Create **Web Service** on Render from this repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python -m src.worker_main`
4. Add environment variables (см. список выше).

## 🧷 Vercel setup (manual)

1. Import repo in Vercel.
2. Ensure Next.js is detected (App Router in `app/api/telegram`).
3. Add Vercel env vars (`RENDER_WORKER_URL`, `WORKER_AUTH_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`).

## 🧱 Folder structure (key modules)

```
app/api/telegram/route.ts      # Vercel webhook
src/worker/app.py              # Render worker API
src/handlers/telegram_worker.py
src/clients/telegram_api.py
src/services/dadata.py
src/services/scoring.py
src/services/risks.py
src/storage/memory_store.py
```

## 🧩 Assumptions

- DaData endpoint: `/suggestions/api/4_1/rs/findById/party`.
- Флаги массового адреса/директора используются только если приходят в ответе DaData.

## 📄 License

MIT
