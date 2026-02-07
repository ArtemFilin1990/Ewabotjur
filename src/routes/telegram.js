const express = require('express');

const router = express.Router();
const webhookSecret = process.env.TELEGRAM_WEBHOOK_SECRET;

router.post('/:secret', (req, res) => {
  const { secret } = req.params;

  if (!webhookSecret || secret !== webhookSecret) {
    return res.status(401).json({ ok: false, error: 'Unauthorized' });
  }

  const update = req.body || {};
  return res.status(200).json({ ok: true, received: update });
});

module.exports = router;
