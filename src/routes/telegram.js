const express = require('express');
const { config } = require('../config');
const { sendTelegramMessage } = require('../services/telegram');
const { logError, logInfo, logWarn } = require('../utils/logger');

const router = express.Router();

/**
 * @param {import('express').Request} req
 * @param {import('express').Response} res
 * @returns {Promise<void>}
 */
router.post(['/', '/:secret'], async (req, res) => {
  if (!config.telegramAvailable) {
    logWarn('Telegram webhook is disabled', {
      operation: 'telegram.webhook',
      result: 'disabled',
    });
    return res.status(503).json({ ok: false, error: 'telegram module is disabled' });
  }

  const { secret } = req.params;
  const headerSecret = req.get('x-telegram-bot-api-secret-token');
  const providedSecret = headerSecret || secret;

  if (config.telegramWebhookSecret) {
    if (providedSecret !== config.telegramWebhookSecret) {
      return res.status(401).json({ ok: false, error: 'Unauthorized' });
    }
  } else if (!config.telegramAllowInsecure) {
    return res.status(401).json({ ok: false, error: 'Unauthorized' });
  } else {
    logWarn('Telegram webhook secret is not configured', {
      operation: 'telegram.webhook',
      result: 'insecure',
    });
  }

  const update = req.body || {};
  const message = update.message;
  if (!message || !message.chat || typeof message.chat.id !== 'number') {
    logWarn('Telegram update without chat id', {
      operation: 'telegram.webhook',
      result: 'ignored',
    });
    return res.status(200).json({ ok: true, ignored: true });
  }

  const text = typeof message.text === 'string' ? message.text.trim() : '';
  const replyText = text ? `Вы написали: ${text}` : 'Бот на связи. Напишите сообщение.';

  try {
    await sendTelegramMessage(message.chat.id, replyText);
    logInfo('Telegram message processed', {
      operation: 'telegram.webhook',
      result: 'success',
    });
    return res.status(200).json({ ok: true });
  } catch (error) {
    logError('Failed to send Telegram message', {
      operation: 'telegram.sendMessage',
      result: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    return res.status(200).json({ ok: false });
  }
});

module.exports = router;
