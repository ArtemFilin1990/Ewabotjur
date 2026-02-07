const express = require('express');
const telegramRouter = require('./routes/telegram');
const bitrixRouter = require('./routes/bitrix');

const app = express();

app.use(express.json());

app.get('/', (_req, res) => {
  res.status(200).send('OK');
});

app.use('/webhook/telegram', telegramRouter);
app.use('/bitrix', bitrixRouter);

app.use((req, res) => {
  res.status(404).json({ error: 'Not Found', path: req.path });
});

module.exports = app;
