# Ewabotjur — Telegram Jurist Bot + Bitrix24 Integration

Production-ready bot with Telegram webhook + Bitrix24 imbot integration, running on Amvera.

## Features

- **Telegram Bot**: Company verification via DaData, contract risk analysis
- **Bitrix24 Integration**: OAuth flow + imbot messaging + auto-refresh tokens
- **DaData Integration**: Company data lookup by INN
- **GPT Analysis**: Conclusions and recommendations (facts from DaData only)
- **Webhook-based**: Secure webhooks for Telegram and Bitrix24
- **Amvera-ready**: Dockerfile + amvera.yml configuration

## Architecture

```
┌─────────────┐
│  Telegram   │ ──── HTTPS Webhook ───┐
└─────────────┘                       │
                                      ▼
┌─────────────┐              ┌──────────────┐
│  Bitrix24   │ ──── OAuth ──▶   FastAPI    │
│   imbot     │              │  (port 3000) │
└─────────────┘              └──────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              ┌──────────┐      ┌──────────┐     ┌──────────┐
              │  DaData  │      │ OpenAI   │     │ Storage  │
              │   API    │      │   GPT    │     │  (JSON)  │
              └──────────┘      └──────────┘     └──────────┘
```

## Telegram Commands

| Command | Description |
| --- | --- |
| `/start` | Help text |
| `/help` | Commands list |
| `/ping` | `pong` response |
| `/company_check <ИНН>` | DaData company card + GPT risk analysis |
| `/risks` | Risk table for pasted text or last uploaded document |
| `/clear_memory` | Clear chat memory |
| `/new_task` | Reset task context (keep prefs) |

## Bitrix24 Integration

Send a message with an INN (10 or 12 digits) to the Bitrix24 imbot, and it will:
1. Extract the INN from your message
2. Lookup company data from DaData
3. Generate GPT analysis (conclusions and recommendations only)
4. Reply with complete analysis in the same chat

## Access Control

Telegram commands are gated by `ALLOWED_CHAT_IDS`. If empty, all access is denied (safe default).

Bitrix24 messages are authenticated via OAuth tokens stored securely.

## Quick Start (Amvera Deployment)

See [AMVERA_DEPLOYMENT.md](AMVERA_DEPLOYMENT.md) for complete deployment guide.

**Quick steps:**
1. Deploy to Amvera (Docker toolchain auto-detected)
2. Set environment variables (see `.env.example`)
3. Setup Telegram webhook: `curl "https://api.telegram.org/bot<TOKEN>/setWebhook" -d "url=https://<app>.amvera.app/webhook/telegram/<SECRET>"`
4. Setup Bitrix24 OAuth (see deployment guide)
5. Test `/health` endpoint

## Environment Variables

See [.env.example](./.env.example) for the complete list.

**Critical variables:**
- `TELEGRAM_BOT_TOKEN` - from @BotFather
- `TG_WEBHOOK_SECRET` - random 32+ char string
- `ALLOWED_CHAT_IDS` - comma-separated chat IDs
- `DADATA_TOKEN` - from dadata.ru
- `OPENAI_API_KEY` - from platform.openai.com
- `BITRIX_CLIENT_ID`, `BITRIX_CLIENT_SECRET` - from Bitrix24 app
- `BITRIX_DOMAIN` - your Bitrix24 portal URL
- `PORT` - set by Amvera (default: 3000)

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the FastAPI server
python -m src.main
```

The server will start on `http://localhost:3000`.

Test with: `curl http://localhost:3000/health`

## Security

See [SECURITY.md](SECURITY.md) for:
- Secret management practices
- Key rotation procedures
- Git history cleanup guide
- Logging best practices

**Important:**
- Never commit secrets to git
- All secrets must be in environment variables only
- Rotate keys if accidentally exposed
- Review logs for sensitive data

## Testing

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_security -v
```

## Documentation

- [AMVERA_DEPLOYMENT.md](AMVERA_DEPLOYMENT.md) - Complete Amvera deployment guide
- [SECURITY.md](SECURITY.md) - Security practices and procedures
- [AGENTS.md](AGENTS.md) - Instructions for AI coding agents
- `.env.example` - Environment variable reference

## API Endpoints

- `GET /health` - Health check
- `POST /webhook/telegram/{secret}` - Telegram webhook (requires TG_WEBHOOK_SECRET)
- `POST /webhook/bitrix` - Bitrix24 events webhook
- `GET /oauth/bitrix/callback` - Bitrix24 OAuth callback

## Architecture Decisions

**Why webhooks instead of polling?**
- Lower latency
- Better scalability
- Required for Amvera deployment

**Why DaData for facts, GPT for analysis?**
- Prevents GPT hallucinations
- Ensures data accuracy
- GPT only provides conclusions/recommendations

**Why JSON token storage?**
- Simple for MVP
- File permissions (0o600) for basic security
- Easy to migrate to DB later

## Known Limitations

- Token storage in files (migrate to DB for production scale)
- No automatic Bitrix24 bot registration (manual OAuth flow)
- OCR for images not implemented
- Risk analysis uses deterministic templates
