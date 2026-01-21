# Ewabotjur TG + MCP DaData (starter)

## What it is
- `mcp-dadata`: MCP server exposing DaData tools (findById/party, suggest/party).
- `tg-bot`: Telegram bot that talks to DaData ONLY via MCP (stdio), stores case fields, supports upload (stores file_id), wizard, and generates markdown bundles.

## Quick start
### 1) MCP DaData
```bash
cd mcp-dadata
npm i
cp .env.example .env
# set DADATA_API_KEY
npm run build
npm start
```

### 2) Telegram bot
```bash
cd ../tg-bot
npm i
cp .env.example .env
# set TELEGRAM_BOT_TOKEN
# ensure MCP_DADATA_ARGS points to ../mcp-dadata/dist/index.js
node src/bot.ts
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
