"""
Тесты для конфигурации
"""
import unittest
import os
from unittest.mock import patch
from src.config import Settings


class TestConfig(unittest.TestCase):
    """Тесты конфигурации приложения"""
    
    @patch.dict(os.environ, {
        "PORT": "8080",
        "LOG_LEVEL": "DEBUG",
        "TELEGRAM_BOT_TOKEN": "test_token",
        "TG_WEBHOOK_SECRET": "test_secret",
    }, clear=True)
    def test_settings_from_env(self):
        """Тест загрузки настроек из переменных окружения"""
        settings = Settings()
        self.assertEqual(settings.port, 8080)
        self.assertEqual(settings.log_level, "DEBUG")
        self.assertEqual(settings.telegram_bot_token, "test_token")
        self.assertEqual(settings.tg_webhook_secret, "test_secret")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_settings_defaults(self):
        """Тест значений по умолчанию"""
        settings = Settings()
        self.assertEqual(settings.port, 3000)
        self.assertEqual(settings.log_level, "INFO")
        self.assertEqual(settings.openai_model, "gpt-4")
    
    @patch.dict(os.environ, {
        "APP_URL": "https://test.amvera.app",
        "TG_WEBHOOK_SECRET": "secret123",
    }, clear=True)
    def test_telegram_webhook_url(self):
        """Тест формирования URL для Telegram webhook"""
        settings = Settings()
        expected = "https://test.amvera.app/webhook/telegram/secret123"
        self.assertEqual(settings.telegram_webhook_url, expected)

    @patch.dict(os.environ, {
        "APP_URL": "https://test.amvera.app",
        "TELEGRAM_WEBHOOK_SECRET": "telegram_secret",
    })
    def test_telegram_webhook_url_from_telegram_secret(self):
        """Тест формирования URL когда используется TELEGRAM_WEBHOOK_SECRET"""
        settings = Settings()
        expected = "https://test.amvera.app/webhook/telegram/telegram_secret"
        self.assertEqual(settings.telegram_webhook_url, expected)

    @patch.dict(os.environ, {
        "TELEGRAM_BOT_TOKEN": "token",
        "TG_WEBHOOK_SECRET": "secret",
        "DADATA_API_KEY": "key",
        "DADATA_SECRET_KEY": "secret",
        "OPENAI_API_KEY": "key",
        "BITRIX_DOMAIN": "https://test.bitrix24.ru",
        "BITRIX_CLIENT_ID": "id",
        "BITRIX_CLIENT_SECRET": "secret",
        "BITRIX_REDIRECT_URL": "https://test.app/callback",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
    })
    def test_validate_required_all_present(self):
        """Тест валидации когда все переменные есть"""
        settings = Settings()
        missing = settings.validate_required()
        self.assertEqual(len(missing), 0)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_required_all_missing(self):
        """Тест валидации когда переменные отсутствуют"""
        settings = Settings()
        missing = settings.validate_required()
        self.assertGreater(len(missing), 0)
        self.assertIn("TELEGRAM_BOT_TOKEN", missing)
        self.assertIn("DADATA_API_KEY", missing)


if __name__ == "__main__":
    unittest.main()
