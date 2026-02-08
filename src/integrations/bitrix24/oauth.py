"""
Bitrix24 OAuth 2.0 интеграция с автоматическим обновлением токенов
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import httpx

from src.config import settings
from src.storage.bitrix_tokens import (
    ensure_schema,
    load_latest_tokens,
    save_tokens,
    BitrixTokenRecord,
)

logger = logging.getLogger(__name__)


class BitrixOAuthManager:
    """
    Менеджер OAuth для Bitrix24 с автоматическим обновлением токенов
    
    ВАЖНО для продакшена на Amvera:
    - Токены хранятся в PostgreSQL (таблица bitrix_tokens)
    - Требуется настроить DATABASE_URL в переменных окружения
    """
    
    def __init__(self):
        self.domain = settings.bitrix_domain
        self.client_id = settings.bitrix_client_id
        self.client_secret = settings.bitrix_client_secret
        self.redirect_url = settings.bitrix_redirect_url
        self.database_url = settings.database_url
    
    def get_auth_url(self) -> str:
        """
        Генерация URL для OAuth авторизации
        
        Returns:
            URL для перенаправления пользователя
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_url,
            "response_type": "code",
            "scope": "imbot"  # Scope для работы с imbot
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.domain}/oauth/authorize/?{query_string}"
        
        logger.info(
            "Generated OAuth URL",
            extra={"operation": "bitrix.oauth.url", "result": "success"},
        )
        return auth_url
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Обмен authorization code на access и refresh токены
        
        Args:
            code: Authorization code из callback
            
        Returns:
            Словарь с токенами
        """
        url = f"{self.domain}/oauth/token/"
        
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_url
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                
                token_data = response.json()
                
                # Сохранение токенов
                await save_tokens(token_data, self.domain)
                
                logger.info(
                    "Successfully exchanged code for tokens",
                    extra={"operation": "bitrix.oauth.exchange", "result": "success"},
                )
                return token_data
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "OAuth token exchange error",
                extra={
                    "operation": "bitrix.oauth.exchange",
                    "result": "error",
                    "status_code": e.response.status_code,
                },
            )
            raise
        except Exception as e:
            logger.error(
                "Error exchanging code for tokens",
                extra={"operation": "bitrix.oauth.exchange", "result": "error"},
                exc_info=True,
            )
            raise
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Обновление access токена с помощью refresh токена
        
        Returns:
            Новые токены
        """
        tokens = await self._load_tokens()

        if not tokens or not tokens.refresh_token:
            raise ValueError("No refresh token available")
        
        url = f"{self.domain}/oauth/token/"
        
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": tokens.refresh_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                
                new_tokens = response.json()
                
                # Сохранение новых токенов
                await save_tokens(new_tokens, self.domain)
                
                logger.info(
                    "Successfully refreshed access token",
                    extra={"operation": "bitrix.oauth.refresh", "result": "success"},
                )
                return new_tokens
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "Token refresh error",
                extra={
                    "operation": "bitrix.oauth.refresh",
                    "result": "error",
                    "status_code": e.response.status_code,
                },
            )
            raise
        except Exception as e:
            logger.error(
                "Error refreshing token",
                extra={"operation": "bitrix.oauth.refresh", "result": "error"},
                exc_info=True,
            )
            raise
    
    async def get_valid_access_token(self) -> str:
        """
        Получение валидного access токена (с автообновлением при необходимости)
        
        Returns:
            Валидный access token
        """
        tokens = await self._load_tokens()

        if not tokens:
            raise ValueError("No tokens available. Please complete OAuth flow first.")
        
        # Проверка истечения токена
        if self._is_token_expired(tokens):
            logger.info(
                "Access token expired, refreshing",
                extra={"operation": "bitrix.oauth.refresh", "result": "start"},
            )
            tokens = await self._load_tokens()

        return tokens.access_token

    async def _load_tokens(self) -> BitrixTokenRecord | None:
        """Загрузка токенов из базы данных."""
        try:
            return await load_latest_tokens(self.domain)
        except Exception:
            logger.error(
                "Error loading tokens from database",
                extra={"operation": "bitrix.oauth.load", "result": "error"},
                exc_info=True,
            )
            return None
    
    def _is_token_expired(self, tokens: BitrixTokenRecord) -> bool:
        """
        Проверка истечения токена
        
        Args:
            tokens: Словарь с токенами
            
        Returns:
            True если токен истек
        """
        saved_at = tokens.saved_at
        expires_in = int(tokens.expires_in)

        # Обновляем токен за 5 минут до истечения
        buffer_seconds = max(expires_in - 300, 0)
        expiry_time = saved_at + timedelta(seconds=buffer_seconds)

        return datetime.now(saved_at.tzinfo) >= expiry_time

    async def ensure_storage_ready(self) -> None:
        """Ensure storage schema exists."""
        await ensure_schema()


# Глобальный экземпляр менеджера
oauth_manager = BitrixOAuthManager()


# Вспомогательные функции для использования в FastAPI endpoints
def initiate_oauth() -> str:
    """Инициация OAuth процесса"""
    return oauth_manager.get_auth_url()


async def handle_oauth_callback(code: str) -> Dict[str, Any]:
    """Обработка OAuth callback"""
    return await oauth_manager.exchange_code_for_tokens(code)


async def get_access_token() -> str:
    """Получение валидного access токена"""
    return await oauth_manager.get_valid_access_token()
