# Production Deployment Checklist

## ✅ Pre-Deployment Checks

### Code Quality
- [x] All tests passing (`pytest` for Python)
- [x] Error handling implemented for all external API calls
- [x] Input validation added (message length limits)
- [x] Timeout handling for network requests
- [x] Proper logging with structured JSON format
- [x] No secrets in code or git history
- [x] `.gitignore` configured properly (storage/, .env, etc.)
- [x] HTTP client connection pooling optimized

### Security
- [x] HTTPS enabled (Amvera provides automatically)
- [x] Webhook secret validation implemented
- [x] API keys stored in environment variables
- [x] Input sanitization (length limits, INN validation)
- [x] Rate limiting consideration (handled by external APIs)
- [x] Error messages don't expose sensitive information

### Configuration
- [x] All required environment variables documented
- [x] `.env.example` file updated with all variables
- [x] Default values set for optional variables
- [x] Configuration validation on startup

### Dependencies
- [x] All dependencies listed in `requirements.txt` (Python)
- [ ] Dependencies audit completed (`pip-audit` or `safety check`)
- [ ] No known vulnerabilities in dependencies

## 🚀 Deployment Steps

### 1. Amvera Setup
- [ ] Amvera account created
- [ ] Repository connected
- [ ] Deployment via `amvera.yml` (Python runtime) succeeds
- [ ] Application deployed

### 2. Environment Variables
Required variables to set in Amvera:
- [ ] `TELEGRAM_BOT_TOKEN`
- [ ] `TG_WEBHOOK_SECRET` (or `TELEGRAM_WEBHOOK_SECRET`)
- [ ] `DADATA_API_KEY`
- [ ] `DADATA_SECRET_KEY`
- [ ] `OPENAI_API_KEY`
- [ ] `BITRIX_DOMAIN`
- [ ] `BITRIX_CLIENT_ID`
- [ ] `BITRIX_CLIENT_SECRET`
- [ ] `BITRIX_REDIRECT_URL`

Optional variables:
- [ ] `APP_URL` (should be your Amvera app URL)
- [ ] `LOG_LEVEL` (default: INFO)
- [ ] `OPENAI_MODEL` (default: gpt-4)
- [ ] `PORT` (Amvera sets automatically, default: 3000)

### 3. External Services Configuration

#### Telegram
- [ ] Bot created via @BotFather
- [ ] Webhook configured: `POST https://api.telegram.org/bot<TOKEN>/setWebhook`
- [ ] Webhook URL: `https://your-app.amvera.io/webhook/telegram/<SECRET>`
- [ ] Webhook verified: `getWebhookInfo` shows correct URL
- [ ] Test message sent and received

#### DaData
- [ ] Account created at dadata.ru
- [ ] API key and secret obtained
- [ ] Sufficient quota available
- [ ] Test request successful

#### OpenAI
- [ ] Account created at platform.openai.com
- [ ] API key created (starts with `sk-`)
- [ ] Billing configured
- [ ] Sufficient credits available
- [ ] Model access confirmed (gpt-4 or gpt-3.5-turbo)

#### Bitrix24
- [ ] Local application created
- [ ] Client ID and Client Secret obtained
- [ ] Redirect URL configured in Bitrix24
- [ ] OAuth flow tested: `/oauth/bitrix/start`
- [ ] Tokens stored (consider persistent storage!)

### 4. Testing

#### Health Checks
- [ ] `/` endpoint returns 200 OK
- [ ] `/health` endpoint returns healthy status
- [ ] All flags in `/health` are true

#### Telegram Bot Testing
- [ ] `/start` command works
- [ ] `/help` command works
- [ ] Valid INN returns analysis
- [ ] Invalid INN shows error message
- [ ] Long message rejected (> 1000 chars)
- [ ] Error handling works (test with wrong API keys)

#### Bitrix24 Bot Testing (if configured)
- [ ] OAuth authorization successful
- [ ] Message sent to bot receives response
- [ ] INN analysis works
- [ ] Error handling works

### 5. Monitoring Setup
- [ ] Logs accessible in Amvera Console
- [ ] Log level set appropriately (INFO for production)
- [ ] Structured logging verified (JSON format)
- [ ] Alert system configured (optional)
- [ ] Uptime monitoring configured (optional)

## 🔍 Post-Deployment Verification

### Immediate Checks (within 1 hour)
- [ ] Application running without crashes
- [ ] No error logs appearing
- [ ] Memory usage within limits
- [ ] CPU usage normal
- [ ] Response times acceptable (< 30s)

### Daily Checks (first week)
- [ ] Check error logs daily
- [ ] Monitor API quota usage (DaData, OpenAI)
- [ ] Verify bot responses are accurate
- [ ] Check for any timeouts

### Weekly Checks
- [ ] Review error patterns
- [ ] Check API costs
- [ ] Monitor resource usage trends
- [ ] Update dependencies if needed

## ⚠️ Known Limitations

### Bitrix24 Tokens
**CRITICAL:** Bitrix24 OAuth tokens are stored in `storage/bitrix_tokens.json`
- Containers on Amvera are ephemeral — tokens will be lost on restart!
- **Solutions:**
  1. Configure persistent volume in Amvera for `/app/storage`
  2. Use external storage (PostgreSQL, Redis)
  3. Re-authorize after each deployment

### Rate Limits
- **OpenAI:** Check your tier limits (requests per minute)
- **DaData:** Check your tariff plan (requests per day)
- **Telegram:** 30 messages/second to same user

### Error Recovery
- Network timeouts: 30-60 seconds configured
- Failed requests: User receives error message
- No automatic retries (to avoid double charging)

## 🛠️ Troubleshooting

### Common Issues

#### "Missing required configuration"
**Cause:** Environment variables not set
**Solution:** Add all required variables in Amvera, then restart

#### "Invalid webhook secret"
**Cause:** Secret mismatch between env var and webhook URL
**Solution:** Verify `TG_WEBHOOK_SECRET` matches in both places

#### "OpenAI API error 401"
**Cause:** Invalid API key
**Solution:** Check `OPENAI_API_KEY` is correct

#### "OpenAI API error 429"
**Cause:** Rate limit exceeded
**Solution:** Wait or upgrade OpenAI plan

#### "DaData API error"
**Cause:** Invalid keys or quota exceeded
**Solution:** Check keys and quota at dadata.ru

#### Bitrix24 bot not responding
**Cause:** Tokens expired or lost
**Solution:** Re-authorize at `/oauth/bitrix/start`

## 📊 Performance Metrics

### Expected Response Times
- Health check: < 100ms
- Telegram /start: < 500ms
- INN analysis (full): 10-30 seconds
  - DaData lookup: 1-3s
  - OpenAI analysis: 5-20s
  - Formatting & sending: < 1s

### Resource Usage (typical)
- Memory: 200-500 MB
- CPU: < 5% idle, < 50% under load
- Network: Depends on usage

## 🔐 Security Reminders

### MUST DO:
- ✅ Use strong, random `TG_WEBHOOK_SECRET`
- ✅ Never commit .env file
- ✅ Rotate API keys periodically
- ✅ Monitor logs for suspicious activity
- ✅ Keep dependencies updated

### MUST NOT DO:
- ❌ Don't expose API keys in logs
- ❌ Don't disable webhook secret validation
- ❌ Don't ignore security updates
- ❌ Don't use same secrets across environments

## 📝 Maintenance Tasks

### Monthly
- [ ] Review and rotate secrets
- [ ] Update dependencies
- [ ] Review logs for patterns
- [ ] Check API costs

### Quarterly
- [ ] Security audit
- [ ] Performance review
- [ ] Disaster recovery test
- [ ] Update documentation

## 📞 Support Contacts

- Amvera Support: https://amvera.io/support
- GitHub Issues: https://github.com/ArtemFilin1990/Ewabotjur/issues

## ✅ Deployment Sign-off

- [ ] All checklist items completed
- [ ] Testing successful
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Team notified

**Deployed by:** _____________
**Date:** _____________
**Version/Commit:** _____________
