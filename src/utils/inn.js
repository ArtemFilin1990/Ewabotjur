const VALID_INN_LENGTHS = [10, 12];

/**
 * Extract the first INN (10 or 12 digits) from text.
 * @param {string} text
 * @returns {string | null}
 */
function extractInn(text) {
  if (!text || typeof text !== 'string') return null;
  const match = text.match(/\b\d{10}\b|\b\d{12}\b/);
  return match ? match[0] : null;
}

/**
 * Validate INN format (digits only, 10 or 12 length) and checksum.
 * @param {string} inn
 * @returns {{ ok: boolean, reason?: string }}
 */
function validateInn(inn) {
  if (!/^\d+$/.test(inn)) {
    return { ok: false, reason: 'ИНН должен содержать только цифры' };
  }
  if (!VALID_INN_LENGTHS.includes(inn.length)) {
    return { ok: false, reason: 'ИНН должен содержать 10 или 12 цифр' };
  }

  if (inn.length === 10) {
    const coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8];
    let sum = 0;
    for (let i = 0; i < 9; i++) {
      sum += Number(inn[i]) * coefficients[i];
    }
    if (sum % 11 % 10 !== Number(inn[9])) {
      return { ok: false, reason: 'Неверная контрольная сумма ИНН' };
    }
  }

  if (inn.length === 12) {
    const coefficients11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8];
    let sum11 = 0;
    for (let i = 0; i < 10; i++) {
      sum11 += Number(inn[i]) * coefficients11[i];
    }
    if (sum11 % 11 % 10 !== Number(inn[10])) {
      return { ok: false, reason: 'Неверная контрольная сумма ИНН' };
    }

    const coefficients12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8];
    let sum12 = 0;
    for (let i = 0; i < 11; i++) {
      sum12 += Number(inn[i]) * coefficients12[i];
    }
    if (sum12 % 11 % 10 !== Number(inn[11])) {
      return { ok: false, reason: 'Неверная контрольная сумма ИНН' };
    }
  }

  return { ok: true };
}

module.exports = { extractInn, validateInn };
