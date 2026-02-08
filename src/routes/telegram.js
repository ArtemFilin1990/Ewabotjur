const express = require('express');
const { config } = require('../config');
const { sendTelegramMessage } = require('../services/telegram');
const { findPartyByInn, normalizeParty, logDadataError } = require('../services/dadata');
const { extractInn, validateInn } = require('../utils/inn');
const { logError, logInfo, logWarn } = require('../utils/logger');

const router = express.Router();

/**
 * Format company data returned by DaData into a readable Telegram message.
 * @param {object} party
 * @returns {string}
 */
function formatPartyMessage(party) {
  const lines = ['📊 Информация о компании\n'];
  if (party.name) lines.push(`Название: ${party.name}`);
  if (party.inn) lines.push(`ИНН: ${party.inn}`);
  if (party.kpp) lines.push(`КПП: ${party.kpp}`);
  if (party.ogrn) lines.push(`ОГРН: ${party.ogrn}`);
  if (party.status) lines.push(`Статус: ${party.status}`);
  if (party.okved) lines.push(`ОКВЭД: ${party.okved}`);
  if (party.address) lines.push(`Адрес: ${party.address}`);
  if (party.management) {
    const mgr = typeof party.management === 'object' ? party.management.name || party.management.post : String(party.management);
    if (mgr) lines.push(`Руководитель: ${mgr}`);
  }
  return lines.join('\n');
}

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

  const chatId = message.chat.id;
  const text = typeof message.text === 'string' ? message.text.trim() : '';

  try {
    const replyText = await buildReply(text, chatId);
    await sendTelegramMessage(chatId, replyText);
    logInfo('Telegram message processed', {
      operation: 'telegram.webhook',
      result: 'success',
    });
    return res.status(200).json({ ok: true });
  } catch (error) {
    logError('Failed to process Telegram message', {
      operation: 'telegram.webhook',
      result: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    return res.status(200).json({ ok: false });
  }
});

/**
 * Build a reply for the incoming message text.
 * @param {string} text
 * @param {number} chatId
 * @returns {Promise<string>}
 */
async function buildReply(text, chatId) {
  if (!text) {
    return 'Бот на связи. Отправьте ИНН компании (10 или 12 цифр).';
  }

  if (text.startsWith('/start')) {
    return (
      '👋 Привет! Я бот для анализа контрагентов.\n\n' +
      'Отправьте мне ИНН компании, и я предоставлю:\n' +
      '✅ Данные из ЕГРЮЛ (через DaData)\n' +
      '✅ Основные реквизиты и статус\n\n' +
      'Просто пришлите ИНН (10 или 12 цифр).'
    );
  }

  if (text.startsWith('/help')) {
    return (
      '📋 Как пользоваться:\n\n' +
      '1. Отправьте ИНН компании (10 или 12 цифр)\n' +
      '2. Бот найдёт данные в DaData\n' +
      '3. Вы получите информацию о компании\n\n' +
      'Пример: 7707083893'
    );
  }

  const inn = extractInn(text);
  if (!inn) {
    return (
      '❌ Не найден ИНН в вашем сообщении.\n' +
      'Пожалуйста, отправьте ИНН (10 или 12 цифр).\n\n' +
      'Пример: 7707083893'
    );
  }

  const validation = validateInn(inn);
  if (!validation.ok) {
    return `❌ Некорректный ИНН: ${inn}\n${validation.reason}`;
  }

  if (!config.dadataAvailable) {
    return `ИНН ${inn} принят, но модуль DaData не настроен. Обратитесь к администратору.`;
  }

  try {
    const raw = await findPartyByInn(inn, { count: config.dadataCount });
    const party = normalizeParty(raw);
    if (!party) {
      return `❌ Компания с ИНН ${inn} не найдена в базе данных.\nПроверьте правильность ИНН.`;
    }
    logInfo('DaData party resolved via Telegram', {
      operation: 'telegram.inn',
      result: 'success',
      inn,
    });
    return formatPartyMessage(party);
  } catch (error) {
    logDadataError(error, { operation: 'telegram.inn', inn });
    return `❌ Ошибка при запросе данных по ИНН ${inn}.\nПопробуйте позже.`;
  }
}

module.exports = router;
