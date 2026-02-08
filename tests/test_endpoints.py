"""
Тесты для FastAPI endpoints приложения
"""
import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from src.main import app


class TestEndpoints(unittest.TestCase):
    """Тесты HTTP endpoints"""

    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_root(self):
        """GET / возвращает информацию о сервисе"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], "Ewabotjur")
        self.assertEqual(data["status"], "running")

    def test_health(self):
        """GET /health возвращает {"status": "ok"}"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("src.main.settings")
    def test_telegram_webhook_invalid_secret(self, mock_settings):
        """POST /webhook/telegram/{secret} с неверным секретом → 403"""
        mock_settings.tg_webhook_secret = "real_secret"
        response = self.client.post("/webhook/telegram/wrong_secret")
        self.assertEqual(response.status_code, 403)

    @patch("src.main.handle_telegram_update", new_callable=AsyncMock)
    @patch("src.main.settings")
    def test_telegram_webhook_valid_secret(self, mock_settings, mock_handler):
        """POST /webhook/telegram/{secret} с валидным секретом → 200"""
        mock_settings.tg_webhook_secret = "test_secret"
        mock_handler.return_value = None

        response = self.client.post(
            "/webhook/telegram/test_secret",
            json={"update_id": 123, "message": {"text": "hello"}},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        mock_handler.assert_awaited_once()

    def test_oauth_bitrix_callback_missing_code(self):
        """GET /oauth/bitrix/callback без code → 400"""
        response = self.client.get("/oauth/bitrix/callback")
        self.assertEqual(response.status_code, 400)

    def test_oauth_bitrix_callback_with_error(self):
        """GET /oauth/bitrix/callback?error=access_denied → 400"""
        response = self.client.get("/oauth/bitrix/callback?error=access_denied")
        self.assertEqual(response.status_code, 400)

    def test_request_id_header(self):
        """Ответ содержит заголовок X-Request-ID"""
        response = self.client.get("/health")
        self.assertIn("x-request-id", response.headers)

    def test_request_id_forwarded(self):
        """Входящий X-Request-ID возвращается в ответе"""
        response = self.client.get(
            "/health", headers={"X-Request-ID": "test-req-123"}
        )
        self.assertEqual(response.headers["x-request-id"], "test-req-123")


if __name__ == "__main__":
    unittest.main()
