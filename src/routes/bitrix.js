const express = require('express');
const { config } = require('../config');
const { logInfo, logWarn } = require('../utils/logger');

const router = express.Router();

router.get('/install', (_req, res) => {
  res.status(200).json({
    status: config.bitrixAvailable ? 'ready' : 'disabled',
    enabled: config.bitrixEnabled,
    hasClientId: Boolean(config.bitrixClientId),
    hasClientSecret: Boolean(config.bitrixClientSecret),
  });
});

/**
 * @param {import('express').Request} req
 * @param {import('express').Response} res
 */
function handleBitrixEvent(req, res) {
  if (!config.bitrixAvailable) {
    logWarn('Bitrix handler is disabled', {
      operation: 'bitrix.event',
      result: 'disabled',
    });
    return res.status(503).json({ ok: false, error: 'bitrix module is disabled' });
  }

  const payload = req.body || {};
  logInfo('Bitrix event received', {
    operation: 'bitrix.event',
    result: 'success',
  });
  return res.status(200).json({ ok: true, received: payload });
}

router.post('/handler', handleBitrixEvent);
router.post('/event', handleBitrixEvent);

module.exports = router;
