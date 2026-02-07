const axios = require('axios');
const { config, requireEnv } = require('../config');
const { logError } = require('../utils/logger');

const DADATA_TIMEOUT_MS = Math.round(config.httpTimeoutSeconds * 1000);

/**
 * @param {string} inn
 * @param {{ count?: number, timeoutMs?: number }} [options]
 * @returns {Promise<unknown>}
 */
async function findPartyByInn(inn, options = {}) {
  const apiKey = requireEnv('DADATA_API_KEY');
  const secret = requireEnv('DADATA_SECRET_KEY');
  const count = options.count ?? config.dadataCount;
  const timeoutMs = options.timeoutMs ?? DADATA_TIMEOUT_MS;

  const response = await axios.post(
    config.dadataUrl,
    { query: String(inn), count },
    {
      timeout: timeoutMs,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        Authorization: `Token ${apiKey}`,
        'X-Secret': secret,
      },
    },
  );

  return response.data;
}

/**
 * @param {unknown} dadataResponse
 * @returns {null | {
 *  name: string | null,
 *  inn: string | null,
 *  kpp: string | null,
 *  ogrn: string | null,
 *  status: string | null,
 *  okved: string | null,
 *  address: string | null,
 *  management: unknown,
 *  phones: unknown[],
 *  emails: unknown[]
 * }}
 */
function normalizeParty(dadataResponse) {
  const suggestion = dadataResponse?.suggestions?.[0];
  if (!suggestion) return null;

  const data = suggestion.data || {};
  return {
    name: data?.name?.short_with_opf || suggestion.value || null,
    inn: data.inn || null,
    kpp: data.kpp || null,
    ogrn: data.ogrn || null,
    status: data?.state?.status || null,
    okved: data.okved || null,
    address: data?.address?.unrestricted_value || data?.address?.value || null,
    management: data.management || null,
    phones: Array.isArray(data.phones) ? data.phones : [],
    emails: Array.isArray(data.emails) ? data.emails : [],
  };
}

/**
 * @param {Error} error
 * @param {{ operation: string, inn: string }} context
 */
function logDadataError(error, context) {
  const status = error?.response?.status;
  logError('DaData request failed', {
    operation: context.operation,
    result: 'error',
    inn: context.inn,
    status,
  });
}

module.exports = {
  findPartyByInn,
  normalizeParty,
  logDadataError,
};
