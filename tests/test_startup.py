"""Тесты поведения старта приложения при проблемах с БД."""
import unittest
from unittest.mock import AsyncMock, patch

from src.main import app


class TestStartupLifespan(unittest.IsolatedAsyncioTestCase):
    """Проверка отказоустойчивого старта приложения."""

    @patch("src.main.close_http_client", new_callable=AsyncMock)
    @patch("src.main.migrate", new_callable=AsyncMock)
    @patch("src.main.settings")
    async def test_startup_continues_when_database_not_required(self, mock_settings, mock_migrate, mock_close_http_client):
        """При недоступной БД сервис продолжает старт, если она не обязательна."""
        mock_settings.database_url = "postgresql://user:pass@db:5432/app"
        mock_settings.database_required_on_startup = False
        mock_migrate.side_effect = TimeoutError()

        async with app.router.lifespan_context(app):
            self.assertTrue(True)

        mock_migrate.assert_awaited_once()
        mock_close_http_client.assert_awaited_once()

    @patch("src.main.migrate", new_callable=AsyncMock)
    @patch("src.main.settings")
    async def test_startup_fails_when_database_required(self, mock_settings, mock_migrate):
        """При обязательной БД ошибка миграции прерывает старт."""
        mock_settings.database_url = "postgresql://user:pass@db:5432/app"
        mock_settings.database_required_on_startup = True
        mock_migrate.side_effect = TimeoutError()

        with self.assertRaises(TimeoutError):
            async with app.router.lifespan_context(app):
                self.fail("lifespan context should not be entered")

        mock_migrate.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
