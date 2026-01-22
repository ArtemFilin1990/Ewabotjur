# Ewabotjur — Production Telegram Jurist Bot (Render Background Worker)

Production-ready Telegram bot running in polling mode on Render as a Background Worker.

## Architecture

```
Telegram -> Render Background Worker (aiogram polling)
```

## Commands

| Command | Description |
| --- | --- |
| `/start` | Help text |
| `/help` | Commands list |
| `/ping` | `pong` response |
| `/company_check <ИНН>` | DaData company card + base risk score |
| `/risks` | Risk table for pasted text or last uploaded document |
| `/clear_memory` | Clear chat memory |
| `/new_task` | Reset task context (keep prefs) |

## Access Control

All commands are gated by `ALLOWED_CHAT_IDS`. If the variable is empty, access is denied for all chats (safe default).

## Environment Variables (Render)

| Variable | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | ✅ | Telegram bot token |
| `ALLOWED_CHAT_IDS` | ✅ | Comma-separated Telegram chat IDs |
| `DADATA_TOKEN` | ✅ | DaData API token |
| `DADATA_SECRET` | Optional | DaData secret key |
| `LOG_LEVEL` | Optional | Default `INFO` |
| `HTTP_TIMEOUT_SECONDS` | Optional | Default `15` |
| `MAX_FILE_SIZE_MB` | Optional | Default `15` |
| `MEMORY_DB_PATH` | Optional | Default `./data/memory.sqlite3` |

## Render Deployment (Manual Steps)

1. Create a new **Background Worker** on Render.
2. Runtime: **Python**.
3. Build command: `pip install -r requirements.txt`.
4. Start command: `python -m app.main`.
5. Add the environment variables listed above.

### How to get `ALLOWED_CHAT_IDS`

1. Send a message to your bot.
2. Call `getUpdates` and read `message.chat.id`:

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
```

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN=...
export ALLOWED_CHAT_IDS=...
export DADATA_TOKEN=...
python -m app.main
```

## ASSUMPTIONS

1. **DaData field mapping**: `name.full_with_opf`, `address.unrestricted_value`, `management.name`, and `state.status` are available in the response payload. If not, `TBD` values are shown.
2. **DaData flags**: `mass_address` and `mass_director` fields are used only when present.
3. **File size limit**: default is 15 MB; override with `MAX_FILE_SIZE_MB`.

## Known Limitations / Next Improvements

- OCR for images is not enabled (scaffold only).
- Risk analysis is deterministic and template-driven.
- Consider adding async job queue for heavy analysis.
