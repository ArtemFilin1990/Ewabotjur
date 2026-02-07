# Deployment Checklist

Use this checklist before deploying to production on Amvera.

## Pre-Deployment Security Audit

- [ ] Run secret scan: `git log --all -S"token" --oneline` (should be clean)
- [ ] Verify .env file is in .gitignore: `cat .gitignore | grep "^.env$"`
- [ ] Check no .env in git: `git ls-files | grep .env` (should only show .env.example)
- [ ] Verify no secrets in code: `grep -r "bot[0-9]" src/` (should be empty)
- [ ] Review recent commits for accidental secrets: `git show HEAD`

## Environment Variables Setup

### Required Variables (Must Set)

- [ ] `TELEGRAM_BOT_TOKEN` - Get from @BotFather
- [ ] `TG_WEBHOOK_SECRET` - Generate: `openssl rand -hex 32`
- [ ] `ALLOWED_CHAT_IDS` - Get from Telegram getUpdates
- [ ] `DADATA_TOKEN` - Get from dadata.ru
- [ ] `DADATA_SECRET` - Get from dadata.ru
- [ ] `OPENAI_API_KEY` - Get from platform.openai.com
- [ ] `BITRIX_CLIENT_ID` - Get from Bitrix24 app
- [ ] `BITRIX_CLIENT_SECRET` - Get from Bitrix24 app
- [ ] `BITRIX_DOMAIN` - Your Bitrix24 URL (e.g., https://xxx.bitrix24.ru)
- [ ] `BITRIX_REDIRECT_URL` - Your app callback URL

### Optional Variables (Recommended)

- [ ] `OPENAI_MODEL` - Default: gpt-4o-mini
- [ ] `OPENAI_TEMPERATURE` - Default: 0.7
- [ ] `OPENAI_MAX_TOKENS` - Default: 2000
- [ ] `LOG_LEVEL` - Default: INFO (use WARNING in production)
- [ ] `APP_ENV` - Set to "production"
- [ ] `ENFORCE_TELEGRAM_WHITELIST` - Default: true

## Amvera Deployment

- [ ] Create application in Amvera
- [ ] Select GitHub repository: ArtemFilin1990/Ewabotjur
- [ ] Select branch: main (or your branch)
- [ ] Toolchain auto-detected as Docker
- [ ] All environment variables added
- [ ] Deploy successful
- [ ] Note your app URL: https://<app-name>.amvera.app

## Post-Deployment Verification

### Health Check

- [ ] Test health endpoint:
  ```bash
  curl https://<app-name>.amvera.app/health
  ```
  Expected: `{"status":"ok","app":"jurist-bot","environment":"production"}`

### Telegram Webhook

- [ ] Set webhook:
  ```bash
  curl "https://api.telegram.org/bot<TOKEN>/setWebhook" \
    -d "url=https://<app-name>.amvera.app/webhook/telegram/<SECRET>"
  ```
- [ ] Verify webhook:
  ```bash
  curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
  ```
  Expected: `"url": "https://<app-name>.amvera.app/webhook/telegram/..."`

- [ ] Test Telegram bot:
  - Send `/start` - should get help text
  - Send `/ping` - should get "pong"
  - Send `/company_check 7707083893` - should get company data

### Bitrix24 OAuth

- [ ] Open OAuth URL in browser:
  ```
  https://<bitrix-domain>/oauth/authorize/?client_id=<CLIENT_ID>&response_type=code&redirect_uri=https://<app-name>.amvera.app/oauth/bitrix/callback
  ```
- [ ] Authorize the application
- [ ] Verify redirect to callback with success message
- [ ] Check logs for "bitrix oauth token obtained and stored"
- [ ] Verify token file created (check Amvera logs, not git)

### Bitrix24 Webhook

- [ ] Send message with INN to Bitrix24 bot
- [ ] Verify bot extracts INN and queries DaData
- [ ] Verify GPT analysis returned
- [ ] Verify reply sent to same chat

## Monitoring

- [ ] Check Amvera logs for errors
- [ ] Verify no secrets in logs:
  ```bash
  # In Amvera logs - should NOT see:
  # - Actual token values
  # - API keys
  # - Client secrets
  ```
- [ ] Monitor DaData API usage/balance
- [ ] Monitor OpenAI API usage/balance
- [ ] Set up alerts for error spikes

## Security Post-Deployment

- [ ] Verify tokens are NOT in application logs
- [ ] Verify webhook secret is working (try invalid secret, should 403)
- [ ] Verify ALLOWED_CHAT_IDS works (test with unauthorized user)
- [ ] Verify Bitrix tokens are NOT in git (should only be in runtime)
- [ ] Review SECURITY.md for key rotation schedule

## Backup Plan

- [ ] Document current environment variable values (securely, not in git)
- [ ] Save Bitrix24 OAuth credentials separately
- [ ] Know how to rotate all keys (see SECURITY.md)
- [ ] Have rollback plan (redeploy previous commit)

## Production Hardening (Optional)

- [ ] Enable rate limiting (if Amvera supports)
- [ ] Set up monitoring/alerting (Prometheus, Grafana)
- [ ] Configure log aggregation
- [ ] Set up uptime monitoring
- [ ] Document incident response procedures
- [ ] Schedule regular key rotation (quarterly recommended)

## Completion

- [ ] All checkboxes above completed
- [ ] Application responding to webhooks
- [ ] No errors in logs for 24 hours
- [ ] Team notified of deployment
- [ ] Documentation updated with production URLs

---

## Quick Troubleshooting

**Webhook not working:**
- Verify TG_WEBHOOK_SECRET matches URL
- Check ALLOWED_CHAT_IDS is set
- Review logs for 403 errors

**Bitrix OAuth failed:**
- Verify BITRIX_REDIRECT_URL exactly matches app settings
- Check client_id and client_secret are correct
- Ensure domain includes https://

**DaData errors:**
- Check API token is valid
- Verify account has sufficient balance
- Ensure proper API permissions

**GPT not responding:**
- Verify OpenAI API key is valid
- Check API usage/billing
- Review rate limits

**Token refresh failing:**
- Check Bitrix tokens were saved during OAuth
- Verify file permissions (should be 0o600)
- Try re-authorizing the app

---

Last updated: 2026-02-07
