const express = require('express');
const telegramRouter = require('./routes/telegram');
const bitrixRouter = require('./routes/bitrix');
const dadataRouter = require('./routes/dadata');
const { validateConfig } = require('./config');
const { logInfo, logWarn } = require('./utils/logger');

const app = express();

app.use(express.json());

const configIssues = validateConfig();
if (configIssues.length > 0) {
  logWarn('Configuration validation issues', {
    operation: 'config.validation',
    result: 'warning',
    issues: configIssues,
  });
} else {
  logInfo('Configuration validated', {
    operation: 'config.validation',
    result: 'success',
  });
}

app.get('/', (_req, res) => {
  res.status(200).send('OK');
});

app.use('/webhook/telegram', telegramRouter);
app.use('/bitrix', bitrixRouter);
app.use('/api', dadataRouter);

app.use((req, res) => {
  res.status(404).json({ error: 'Not Found', path: req.path });
});

module.exports = app;
