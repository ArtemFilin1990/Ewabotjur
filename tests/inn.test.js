const assert = require('node:assert/strict');
const test = require('node:test');

const { extractInn, validateInn } = require('../src/utils/inn');

test('extractInn returns null for empty input', () => {
  assert.equal(extractInn(''), null);
  assert.equal(extractInn(null), null);
  assert.equal(extractInn(undefined), null);
});

test('extractInn finds 10-digit INN', () => {
  assert.equal(extractInn('ИНН 7707083893'), '7707083893');
});

test('extractInn finds 12-digit INN', () => {
  assert.equal(extractInn('проверь 500100732259 пожалуйста'), '500100732259');
});

test('extractInn returns first INN when multiple present', () => {
  assert.equal(extractInn('7707083893 и 7710140679'), '7707083893');
});

test('extractInn ignores non-INN digit sequences', () => {
  assert.equal(extractInn('123'), null);
  assert.equal(extractInn('12345678'), null);
});

test('validateInn accepts valid 10-digit INN', () => {
  assert.deepEqual(validateInn('7707083893'), { ok: true });
});

test('validateInn rejects non-digit characters', () => {
  const result = validateInn('770708abc3');
  assert.equal(result.ok, false);
});

test('validateInn rejects wrong length', () => {
  const result = validateInn('12345');
  assert.equal(result.ok, false);
});

test('validateInn rejects 10-digit INN with bad checksum', () => {
  const result = validateInn('7707083890');
  assert.equal(result.ok, false);
});

test('validateInn rejects 12-digit INN with bad checksum', () => {
  const result = validateInn('123456789012');
  assert.equal(result.ok, false);
});
