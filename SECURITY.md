# Security Policy

## Overview

This document outlines security practices and guidelines for the Ewabotjur project.

## Sensitive Data Management

### ✅ What We Do

1. **No Secrets in Code**: All API keys, tokens, and secrets are stored in environment variables
2. **No Secrets in Git History**: Repository has been audited and no secrets found in commit history
3. **Secure .gitignore**: All sensitive file patterns are excluded from version control
4. **Environment Variables Only**: All credentials accessed via `os.getenv()` at runtime

### 🚫 What We Never Do

- Hardcode API keys, tokens, or passwords in source code
- Commit `.env` files or other files containing secrets
- Log sensitive data (tokens, passwords, personal data)
- Store unencrypted tokens in version control

## Required Environment Variables

All environment variables are documented in `.env.example`. Never commit real values to this file - only use placeholders.

### Critical Secrets

These must be set for production:

- `TELEGRAM_BOT_TOKEN` - Telegram Bot API token
- `TG_WEBHOOK_SECRET` - Random secret for webhook URL security
- `DADATA_TOKEN` - DaData API token
- `DADATA_SECRET` - DaData secret key
- `OPENAI_API_KEY` - OpenAI API key
- `BITRIX_CLIENT_ID` - Bitrix24 OAuth client ID
- `BITRIX_CLIENT_SECRET` - Bitrix24 OAuth client secret
- `WORKER_AUTH_TOKEN` - Internal worker authentication token

## Key Rotation Procedures

### When to Rotate Keys

Immediately rotate keys if:
- Keys are accidentally committed to version control
- Keys are exposed in logs or error messages
- A team member with key access leaves the project
- You suspect unauthorized access
- As part of regular security maintenance (quarterly recommended)

### How to Rotate Keys

#### Telegram Bot Token
```bash
# 1. Get new token from @BotFather using /token command
# 2. Update TELEGRAM_BOT_TOKEN in Amvera environment variables
# 3. Restart the application
# 4. Update webhook with new token
curl -s "https://api.telegram.org/bot<NEW_TOKEN>/setWebhook" \
  -d "url=https://<app-name>.amvera.app/webhook/telegram/<TG_WEBHOOK_SECRET>"
```

#### DaData API Keys
```bash
# 1. Generate new keys in DaData dashboard
# 2. Update DADATA_TOKEN and DADATA_SECRET in Amvera
# 3. Restart the application
# 4. Revoke old keys in DaData dashboard
```

#### OpenAI API Key
```bash
# 1. Create new API key in OpenAI platform
# 2. Update OPENAI_API_KEY in Amvera
# 3. Restart the application
# 4. Delete old key from OpenAI platform
```

#### Bitrix24 OAuth Credentials
```bash
# 1. Regenerate client secret in Bitrix24 application settings
# 2. Update BITRIX_CLIENT_SECRET in Amvera
# 3. Restart the application
# 4. Re-authorize the application (visit OAuth URL)
```

#### Webhook Secret
```bash
# 1. Generate new random secret: openssl rand -hex 32
# 2. Update TG_WEBHOOK_SECRET in Amvera
# 3. Restart the application
# 4. Update Telegram webhook URL with new secret
```

## Git History Cleanup

If secrets were accidentally committed:

### Using git-filter-repo (Recommended)

```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove file containing secrets
git filter-repo --path path/to/secret/file --invert-paths

# Remove specific patterns
git filter-repo --replace-text <(echo "SECRET_VALUE==>REDACTED")

# Force push (DESTRUCTIVE - coordinate with team)
git push --force --all
```

### Using BFG Repo-Cleaner (Alternative)

```bash
# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Remove secrets
java -jar bfg-1.14.0.jar --delete-files secret.env
java -jar bfg-1.14.0.jar --replace-text passwords.txt

# Force push
git push --force --all
```

### After History Cleanup

**CRITICAL**: After cleaning git history:

1. ✅ Rotate ALL exposed secrets immediately
2. ✅ Notify all team members to re-clone the repository
3. ✅ Update all deployment environments with new secrets
4. ✅ Verify secrets are not accessible in old commits on GitHub
5. ✅ Monitor for unauthorized access using old credentials

## Logging Best Practices

### ✅ Safe Logging

```python
logger.info(
    "telegram webhook accepted",
    extra={
        "request_id": request_id,
        "status_code": 200,
        "has_token": bool(config.telegram_bot_token),  # ✅ Boolean, not value
    }
)
```

### 🚫 Unsafe Logging

```python
# NEVER DO THIS
logger.info(f"Using token: {config.telegram_bot_token}")  # ❌ Exposes secret
logger.debug(f"Request headers: {request.headers}")  # ❌ May contain Authorization
```

### Log Sanitization

The application automatically:
- Excludes token values from logs
- Uses request IDs instead of personal identifiers
- Logs only success/failure status, not sensitive payloads

## Data Privacy

### Personal Data

The application may process:
- Telegram chat IDs (used for access control)
- Company data from DaData (ИНН, ОГРН, company names)
- Messages from users

### Privacy Measures

- Chat IDs are checked against whitelist (`ALLOWED_CHAT_IDS`)
- No personal data is stored permanently
- DaData queries use company IDs (ИНН), not personal names
- GPT prompts exclude personal identifiable information

### GDPR Compliance

When deploying in EU:
- Enable `LOG_LEVEL=WARNING` to minimize data in logs
- Regularly clear temporary storage (`./storage/`, `./data/`)
- Implement data retention policies
- Add user consent mechanisms for data processing

## Vulnerability Reporting

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email the maintainer directly (check repository)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

Expected response time: 48 hours

## Security Checklist for Deployment

Before deploying to production:

- [ ] All secrets set as environment variables in Amvera
- [ ] `.env.example` contains no real secrets
- [ ] No secrets in git history (`git log --all -S"secret_pattern"`)
- [ ] `.gitignore` includes all sensitive file patterns
- [ ] Webhook secrets are random and strong (32+ characters)
- [ ] `ALLOWED_CHAT_IDS` is set (not empty)
- [ ] HTTPS is enforced for all webhooks
- [ ] Logs reviewed for exposed secrets
- [ ] Token rotation schedule established
- [ ] Team trained on security practices

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Secrets in Git: A Developer's Guide](https://github.blog/2021-04-05-behind-githubs-new-authentication-token-formats/)
- [DaData Security](https://dadata.ru/api/security/)
- [Telegram Bot Security](https://core.telegram.org/bots/webhooks#always-use-secret-token)

## Last Updated

This security policy was last reviewed: 2026-02-07
