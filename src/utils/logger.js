const LEVELS = {
  info: 'info',
  warn: 'warn',
  error: 'error',
};

/**
 * @param {string} level
 * @param {string} message
 * @param {Record<string, unknown>} meta
 * @returns {Record<string, unknown>}
 */
function buildPayload(level, message, meta = {}) {
  return {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...meta,
  };
}

/**
 * @param {string} level
 * @param {string} message
 * @param {Record<string, unknown>} [meta]
 */
function log(level, message, meta) {
  const payload = buildPayload(level, message, meta);
  const line = JSON.stringify(payload);
  if (level === LEVELS.error) {
    console.error(line);
  } else if (level === LEVELS.warn) {
    console.warn(line);
  } else {
    console.log(line);
  }
}

/**
 * @param {string} message
 * @param {Record<string, unknown>} [meta]
 */
function logInfo(message, meta) {
  log(LEVELS.info, message, meta);
}

/**
 * @param {string} message
 * @param {Record<string, unknown>} [meta]
 */
function logWarn(message, meta) {
  log(LEVELS.warn, message, meta);
}

/**
 * @param {string} message
 * @param {Record<string, unknown>} [meta]
 */
function logError(message, meta) {
  log(LEVELS.error, message, meta);
}

module.exports = {
  logInfo,
  logWarn,
  logError,
};
