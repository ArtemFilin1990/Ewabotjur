"""
Тесты для проверки обновления просроченного Bitrix OAuth токена
"""
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from src.integrations.bitrix24.oauth import BitrixOAuthManager
from src.storage.bitrix_tokens import BitrixTokenRecord


class TestGetValidAccessToken(unittest.IsolatedAsyncioTestCase):
    """Тесты get_valid_access_token"""

    @patch("src.integrations.bitrix24.oauth.settings")
    async def test_refresh_called_when_token_expired(self, mock_settings):
        """Expired token must trigger refresh_access_token, not just reload."""
        mock_settings.bitrix_domain = "https://test.bitrix24.ru"
        mock_settings.bitrix_client_id = "id"
        mock_settings.bitrix_client_secret = "secret"
        mock_settings.bitrix_redirect_url = "https://test.app/callback"
        mock_settings.database_url = "postgresql+asyncpg://u:p@localhost/db"

        manager = BitrixOAuthManager()

        expired_record = BitrixTokenRecord(
            access_token="old_token",
            refresh_token="refresh_tok",
            expires_in=3600,
            domain="https://test.bitrix24.ru",
            saved_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )

        manager._load_tokens = AsyncMock(return_value=expired_record)
        manager.refresh_access_token = AsyncMock(
            return_value={"access_token": "new_token", "refresh_token": "new_refresh", "expires_in": 3600}
        )

        token = await manager.get_valid_access_token()

        manager.refresh_access_token.assert_awaited_once()
        self.assertEqual(token, "new_token")

    @patch("src.integrations.bitrix24.oauth.settings")
    async def test_no_refresh_when_token_valid(self, mock_settings):
        """Valid (non-expired) token must be returned without refresh."""
        mock_settings.bitrix_domain = "https://test.bitrix24.ru"
        mock_settings.bitrix_client_id = "id"
        mock_settings.bitrix_client_secret = "secret"
        mock_settings.bitrix_redirect_url = "https://test.app/callback"
        mock_settings.database_url = "postgresql+asyncpg://u:p@localhost/db"

        manager = BitrixOAuthManager()

        valid_record = BitrixTokenRecord(
            access_token="valid_token",
            refresh_token="refresh_tok",
            expires_in=3600,
            domain="https://test.bitrix24.ru",
            saved_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )

        manager._load_tokens = AsyncMock(return_value=valid_record)
        manager.refresh_access_token = AsyncMock()

        token = await manager.get_valid_access_token()

        manager.refresh_access_token.assert_not_awaited()
        self.assertEqual(token, "valid_token")


if __name__ == "__main__":
    unittest.main()
