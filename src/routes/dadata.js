const express = require('express');
const { config, readEnv } = require('../config');
const { findPartyByInn, normalizeParty, logDadataError } = require('../services/dadata');
const { logInfo, logWarn } = require('../utils/logger');

const router = express.Router();

/**
 * @param {string} value
 * @returns {string | null}
 */
function normalizeInn(value) {
  if (!value) return null;
  const trimmed = String(value).trim();
  return trimmed === '' ? null : trimmed;
}

/**
 * @param {string} inn
 * @returns {{ ok: boolean, reason?: string }}
 */
function validateInn(inn) {
  if (!/^\d+$/.test(inn)) {
    return { ok: false, reason: 'inn must contain only digits' };
  }
  if (!config.dadataInnLengths.includes(inn.length)) {
    return { ok: false, reason: 'inn must be 10 or 12 digits long' };
  }
  return { ok: true };
}

router.post('/dadata/party', async (req, res) => {
  if (!config.dadataEnabled) {
    return res.status(503).json({ error: 'dadata module is disabled' });
  }

  const inn = normalizeInn(req.body?.inn || req.body?.query);
  if (!inn) {
    return res.status(400).json({ error: 'inn is required' });
  }

  const validation = validateInn(inn);
  if (!validation.ok) {
    return res.status(400).json({ error: validation.reason });
  }

  const apiKey = readEnv('DADATA_API_KEY');
  const secret = readEnv('DADATA_SECRET_KEY');
  if (!apiKey || !secret) {
    logWarn('DaData configuration missing', {
      operation: 'dadata.party',
      result: 'error',
    });
    return res.status(503).json({ error: 'dadata is not configured' });
  }

  try {
    const raw = await findPartyByInn(inn, { count: config.dadataCount });
    const party = normalizeParty(raw);

    if (!party) {
      logInfo('DaData party not found', {
        operation: 'dadata.party',
        result: 'not_found',
        inn,
      });
      return res.status(404).json({ error: 'not found' });
    }

    logInfo('DaData party resolved', {
      operation: 'dadata.party',
      result: 'success',
      inn,
    });
    return res.json({ party, raw });
  } catch (error) {
    logDadataError(error, { operation: 'dadata.party', inn });
    return res.status(502).json({ error: 'dadata request failed' });
  }
});

module.exports = router;
