# Ewabotjur TG + MCP DaData

## What it is
Telegram bot юрист с интеграцией DaData через MCP (Model Context Protocol).

**Структура проекта:**
- `mcp-dadata`: MCP server exposing DaData tools (findById/party, suggest/party)
- `tg-bot`: Telegram bot that talks to DaData ONLY via MCP (stdio), stores case fields, supports upload (stores file_id), wizard, and generates markdown bundles

**📚 Полная документация:** См. [SRS_Telegram_Bot_Jurist.md](SRS_Telegram_Bot_Jurist.md)

## Configuration

### 1. MCP DaData Server

1. Get your DaData API key from https://dadata.ru/
2. Copy `mcp-dadata/.env.example` to `mcp-dadata/.env`
3. Set `DADATA_API_KEY` in `.env`

### 2. Telegram Bot

1. Create a bot via @BotFather and get your token
2. Copy `tg-bot/.env.example` to `tg-bot/.env`
3. Set `TELEGRAM_BOT_TOKEN` in `.env`
4. Verify `MCP_DADATA_ARGS` points to the correct path

### 3. Build and Run

```bash
# Build MCP server
cd mcp-dadata
npm install
npm run build

# Start bot (in separate terminal)
cd ../tg-bot
npm install
npm start
```

## Bot commands
- /new
- /scenario <name>
- /set key=value
- /get key
- /fields
- /upload_doc (then send a file)
- /upload_att (then send a file)
- /dadata <inn|ogrn> [kpp]
- /wizard
- /generate
- /export_json
