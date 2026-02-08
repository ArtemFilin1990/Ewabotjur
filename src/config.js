const DEFAULT_HTTP_TIMEOUT_SECONDS = 10;
const DEFAULT_DADATA_COUNT = 1;
const DADATA_INN_LENGTHS = [10, 12];

/**
 * @param {string} value
 * @returns {boolean}
 */
function parseBoolean(value) {
  if (value === undefined || value === null || value === '') {
    return false;
  }
  return ['true', '1', 'yes', 'on'].includes(String(value).toLowerCase());
}

/**
 * @param {string | undefined} value
 * @param {number} fallback
 * @returns {number}
 */
function parseNumber(value, fallback) {
  if (value === undefined || value === null || value === '') {
    return fallback;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

/**
 * @param {string | undefined} value
 * @param {number} fallback
 * @returns {number}
 */
function parsePositiveInteger(value, fallback) {
  const parsed = Math.round(parseNumber(value, fallback));
  return parsed > 0 ? parsed : fallback;
}

/**
 * @param {string} name
 * @returns {string | undefined}
 */
function readEnv(name) {
  const value = process.env[name];
  return value && value.trim() !== '' ? value : undefined;
}

/**
 * @param {string} name
 * @returns {string}
 */
function requireEnv(name) {
  const value = readEnv(name);
  if (!value) {
    throw new Error(`Missing env: ${name}`);
  }
  return value;
}

/**
 * @returns {{ issues: string[], missingRequired: string[] }}
 */
function validateConfig() {
  const issues = [];
  const missingRequired = [];
  if (config.httpTimeoutSeconds <= 0) {
    issues.push('HTTP_TIMEOUT_SECONDS must be greater than 0');
  }
  if (config.dadataCount <= 0) {
    issues.push('DADATA_COUNT must be greater than 0');
  }
  if (!config.telegramWebhookSecret) {
    missingRequired.push('TELEGRAM_WEBHOOK_SECRET is not set');
  }
  if (!config.telegramBotToken) {
    missingRequired.push('TELEGRAM_BOT_TOKEN is not set');
  }
  if (config.dadataEnabled) {
    if (!readEnv('DADATA_API_KEY')) {
      missingRequired.push('DADATA_API_KEY is not set');
    }
    if (!readEnv('DADATA_SECRET_KEY')) {
      missingRequired.push('DADATA_SECRET_KEY is not set');
    }
  }
  return { issues, missingRequired };
}

const config = {
  dadataUrl: 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party',
  httpTimeoutSeconds: parseNumber(readEnv('HTTP_TIMEOUT_SECONDS'), DEFAULT_HTTP_TIMEOUT_SECONDS),
  dadataCount: parsePositiveInteger(readEnv('DADATA_COUNT'), DEFAULT_DADATA_COUNT),
  dadataEnabled: parseBoolean(readEnv('ENABLE_DADATA') ?? 'true'),
  dadataInnLengths: DADATA_INN_LENGTHS,
  telegramWebhookSecret: readEnv('TELEGRAM_WEBHOOK_SECRET'),
  telegramBotToken: readEnv('TELEGRAM_BOT_TOKEN'),
};

module.exports = {
  config,
  readEnv,
  requireEnv,
  parseNumber,
  parseBoolean,
  parsePositiveInteger,
  validateConfig,
};
