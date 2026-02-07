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
router.post('/:secret', async (req, res) => {
  const { secret } = req.params;

  if (!config.telegramWebhookSecret || secret !== config.telegramWebhookSecret) {
    return res.status(401).json({ ok: false, error: 'Unauthorized' });
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
