const express = require('express');

const router = express.Router();

router.get('/install', (_req, res) => {
  res.status(200).json({
    status: 'ready',
    hasClientId: Boolean(process.env.BITRIX_CLIENT_ID),
    hasClientSecret: Boolean(process.env.BITRIX_CLIENT_SECRET),
  });
});

router.post('/handler', (req, res) => {
  const payload = req.body || {};
  res.status(200).json({ ok: true, received: payload });
});

module.exports = router;
