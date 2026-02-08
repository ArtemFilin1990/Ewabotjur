const express = require('express');
const telegramRouter = require('./routes/telegram');
const bitrixRouter = require('./routes/bitrix');
const dadataRouter = require('./routes/dadata');
const { validateConfig } = require('./config');
const { logInfo, logWarn, logError } = require('./utils/logger');

const app = express();

app.use(express.json());

const { issues: configIssues, missingRequired, disabledModules } = validateConfig();
if (configIssues.length > 0) {
  logWarn('Configuration validation issues', {
    operation: 'config.validation',
    result: 'warning',
    issues: configIssues,
  });
  throw new Error(`Invalid configuration: ${configIssues.join(', ')}`);
}

if (missingRequired.length > 0) {
  logWarn('Configuration validation warnings', {
    operation: 'config.validation',
    result: 'warning',
    issues: missingRequired,
    disabledModules,
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

app.get('/health', (_req, res) => {
  res.status(200).json({ status: 'ok' });
});

app.use('/webhook/telegram', telegramRouter);
app.use('/bitrix', bitrixRouter);
app.use('/api', dadataRouter);

app.use((req, res) => {
  res.status(404).json({ error: 'Not Found', path: req.path });
});

app.use((err, _req, res, _next) => {
  logError('Unhandled application error', {
    operation: 'app.error',
    result: 'error',
    error: err instanceof Error ? err.message : 'Unknown error',
  });
  res.status(500).json({ error: 'Internal Server Error' });
});

module.exports = app;
