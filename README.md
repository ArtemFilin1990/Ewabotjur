# Ewabotjur — Production Telegram Jurist Bot (Vercel Webhook + Render Worker)

Production-ready Telegram bot with a lightweight Vercel webhook and a Render worker that performs all heavy processing (DaData, file extraction, risk analysis, document generation).

## Architecture

```
Telegram -> Vercel /api/telegram (Next.js) -> Render Worker /ingest (FastAPI)
```

- **Vercel** hosts `app/api/telegram/route.ts` and immediately ACKs updates.
- **Render Worker** processes updates, calls DaData, extracts files, builds risk tables, and replies via Telegram Bot API.

## Commands

| Command | Description |
| --- | --- |
| `/start` | Help text |
| `/help` | Commands list |
| `/ping` | `pong` response |
| `/company_check <ИНН>` | DaData company card + base risk score |
| `/risks` | Risk table for contract text (use reply, inline text, or file) |
| `/clear_memory` | Clear chat memory |
| `/new_task` | Reset task context |

`/risks` supports `file` flag to return a DOCX file: `/risks file`.

## Environment Variables

### Vercel (Webhook Forwarder)

| Variable | Required | Description |
| --- | --- | --- |
| `RENDER_WORKER_URL` | ✅ | Base URL of Render worker (e.g., `https://worker.onrender.com`) |
| `WORKER_AUTH_TOKEN` | ✅ | Shared secret for worker auth |
| `TELEGRAM_WEBHOOK_SECRET` | Optional | Secret header to validate incoming webhook |

### Render (Worker)

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token |
| `ALLOWED_CHAT_IDS` | ✅ | Comma-separated Telegram chat IDs |
| `WORKER_AUTH_TOKEN` | ✅ | Must match Vercel token |
| `DADATA_TOKEN` | ✅ | DaData API token |
| `DADATA_SECRET` | Optional | DaData secret key |
| `LOG_LEVEL` | Optional | Default `INFO` |
| `HTTP_TIMEOUT_SECONDS` | Optional | Default `15` |
| `MAX_FILE_SIZE_MB` | Optional | Default `15` |
| `MEMORY_STORE_PATH` | Optional | Default `./storage/memory.json` |

## Telegram Webhook Setup

Replace `<BOT_TOKEN>` and `<VERCEL_URL>` with your values.

```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://<VERCEL_URL>/api/telegram"
```

To include a secret header, use the `secret_token` parameter and set the same value as `TELEGRAM_WEBHOOK_SECRET`:

```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://<VERCEL_URL>/api/telegram" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

Check webhook status:

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

## Local Development

### Render Worker (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=...
export ALLOWED_CHAT_IDS=...
export WORKER_AUTH_TOKEN=...
export DADATA_TOKEN=...
python -m src.main
```

### Vercel Webhook (Next.js)

```bash
pnpm install
pnpm dev
```

## Render Deployment (Manual Steps)

1. Create a new **Web Service** on Render from this repo.
2. Runtime: **Python**.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python -m src.main`
5. Add environment variables listed in **Render** section above.

You can also use `render.yaml` for a baseline service definition.

## Vercel Deployment (Manual Steps)

1. Import the repo to Vercel.
2. Framework preset: **Next.js**.
3. Set environment variables listed in **Vercel** section above.
4. Deploy and use the Vercel URL in `setWebhook`.

## ASSUMPTIONS

1. **Webhook secret header**: Vercel validates `X-TG-SECRET` (custom) or Telegram's `X-Telegram-Bot-Api-Secret-Token` when `TELEGRAM_WEBHOOK_SECRET` is set.
2. **DaData response**: Optional flags `mass_address` and `mass_director` are used only if present in DaData response; scoring ignores them otherwise.
3. **File size limit**: Default is 15 MB, override with `MAX_FILE_SIZE_MB`.

## Known Limitations / Next Improvements

- OCR for images is scaffolded but not enabled.
- Risk analysis is deterministic; add LLM enrichment if needed.
- Memory is JSON-file based; SQLite can be added for scale.
