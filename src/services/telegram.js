const axios = require('axios');
const { config } = require('../config');

const TELEGRAM_API_BASE = 'https://api.telegram.org';

/**
 * @param {string} token
 * @returns {string}
 */
function buildTelegramApiBaseUrl(token) {
  return `${TELEGRAM_API_BASE}/bot${token}`;
}

/**
 * @param {number} chatId
 * @param {string} text
 * @returns {Promise<void>}
 */
async function sendTelegramMessage(chatId, text) {
  const token = config.telegramBotToken;
  if (!token) {
    throw new Error('TELEGRAM_BOT_TOKEN is not configured');
  }

  const url = `${buildTelegramApiBaseUrl(token)}/sendMessage`;
  await axios.post(
    url,
    { chat_id: chatId, text },
    { timeout: config.httpTimeoutSeconds * 1000 },
  );
}

module.exports = {
  sendTelegramMessage,
};
