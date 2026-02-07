const app = require('./src/app');
const { logInfo } = require('./src/utils/logger');

const PORT = process.env.PORT || 3000;

const server = app.listen(PORT, '0.0.0.0', () => {
  logInfo('Server listening', {
    operation: 'startup',
    result: 'success',
    port: PORT,
  });
});

const stopSignals = ['SIGINT', 'SIGTERM'];
stopSignals.forEach((signal) => {
  process.on(signal, () => {
    server.close(() => process.exit(0));
  });
});
