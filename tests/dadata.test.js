const assert = require('node:assert/strict');
const test = require('node:test');

const { normalizeParty } = require('../src/services/dadata');

test('normalizeParty returns null when no suggestions', () => {
  assert.equal(normalizeParty({}), null);
});

test('normalizeParty maps primary fields', () => {
  const response = {
    suggestions: [
      {
        value: 'ООО Ромашка',
        data: {
          name: { short_with_opf: 'ООО Ромашка' },
          inn: '1234567890',
          kpp: '123456789',
          ogrn: '1234567890123',
          state: { status: 'ACTIVE' },
          okved: '62.01',
          address: { unrestricted_value: 'Москва, ул. Пример' },
          management: { name: 'Иван Иванов' },
          phones: [{ value: '+70000000000' }],
          emails: [{ value: 'test@example.com' }],
        },
      },
    ],
  };

  assert.deepEqual(normalizeParty(response), {
    name: 'ООО Ромашка',
    inn: '1234567890',
    kpp: '123456789',
    ogrn: '1234567890123',
    status: 'ACTIVE',
    okved: '62.01',
    address: 'Москва, ул. Пример',
    management: { name: 'Иван Иванов' },
    phones: [{ value: '+70000000000' }],
    emails: [{ value: 'test@example.com' }],
  });
});
