# Ewabotjur (Node.js)

Минимальный Express-сервер для Telegram webhook и локального приложения Bitrix24. Готов к деплою на Amvera (node + npm).

## Требования
- Node.js 18+
- npm
- Переменные окружения:
  - `PORT` (по умолчанию 3000)
  - `TELEGRAM_WEBHOOK_SECRET`
  - `BITRIX_CLIENT_ID`
  - `BITRIX_CLIENT_SECRET`
  - `DADATA_API_KEY`
  - `DADATA_SECRET_KEY`
  - `HTTP_TIMEOUT_SECONDS` (по умолчанию 10)
  - `ENABLE_DADATA` (по умолчанию true)

## Установка и запуск
```bash
npm install
cp .env.example .env
# заполните .env
npm run start
```
Сервер слушает `process.env.PORT || 3000`.

## Эндпоинты
- `GET /` — health-check, 200 OK
- `POST /webhook/telegram/:secret` — проверяет `TELEGRAM_WEBHOOK_SECRET`, возвращает принятый update
- `GET /bitrix/install` — отвечает готовностью приложения и наличием Bitrix-конфигурации
- `POST /bitrix/handler` — принимает события Bitrix24 и эхо-возвращает тело запроса
- `POST /api/dadata/party` — ищет контрагента по ИНН в DaData (тело `{ "inn": "3525405517" }`)

## Деплой в Amvera
- Конфигурация: `amvera.yml` (environment: node, toolchain: npm, version: 18, command: `node index.js`, containerPort: 3000)
- Установите переменные окружения через UI Amvera (`PORT`, `TELEGRAM_WEBHOOK_SECRET`, `BITRIX_CLIENT_ID`, `BITRIX_CLIENT_SECRET`)

## Настройка Telegram webhook
```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=https://<your-app>.amvera.app/webhook/telegram/<TELEGRAM_WEBHOOK_SECRET>"
```

Проверка статуса webhook (метод Telegram API, а не путь вашего сервера):
```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

Важно: `https://<your-app>.amvera.app/webhook/telegram/<TELEGRAM_WEBHOOK_SECRET>` — это входная точка для POST-запросов Telegram. Если открыть её в браузере (GET), 404/пусто — ожидаемое поведение.

## Bitrix24
- `GET /bitrix/install` можно использовать как endpoint установки локального приложения
- `POST /bitrix/handler` предназначен для входящих событий Bitrix24

## DaData

Для работы эндпоинта `/api/dadata/party` нужны `DADATA_API_KEY` и `DADATA_SECRET_KEY`.

Пример запроса:
```bash
curl -X POST https://<YOUR_DOMAIN>/api/dadata/party \
  -H "Content-Type: application/json" \
  -d '{"inn":"3525405517"}'
```

## Тесты
Отдельные тесты не настроены. Скрипт `npm test` возвращает успешный статус-заглушку.
