"""
Bitrix24 OAuth 2.0 интеграция с автоматическим обновлением токенов
"""
import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class BitrixOAuthManager:
    """
    Менеджер OAuth для Bitrix24 с автоматическим обновлением токенов
    
    ВАЖНО для продакшена на Amvera:
    - Токены хранятся в файле storage/bitrix_tokens.json
    - В контейнере Amvera нужно смонтировать persistent volume для /app/storage
    - Альтернативно: использовать БД (PostgreSQL, Redis) для хранения токенов
    - Без persistent storage токены будут теряться при рестарте контейнера
    """
    
    # Файл для хранения токенов
    # TODO: В продакшене рекомендуется использовать БД или persistent volume
    TOKEN_FILE = "storage/bitrix_tokens.json"
    
    def __init__(self):
        self.domain = settings.bitrix_domain
        self.client_id = settings.bitrix_client_id
        self.client_secret = settings.bitrix_client_secret
        self.redirect_url = settings.bitrix_redirect_url
        
        # Создание директории для хранения токенов
        os.makedirs(os.path.dirname(self.TOKEN_FILE), exist_ok=True)
    
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
                self._save_tokens(token_data)
                
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
        tokens = self._load_tokens()
        
        if not tokens or "refresh_token" not in tokens:
            raise ValueError("No refresh token available")
        
        url = f"{self.domain}/oauth/token/"
        
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": tokens["refresh_token"]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                
                new_tokens = response.json()
                
                # Сохранение новых токенов
                self._save_tokens(new_tokens)
                
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
        tokens = self._load_tokens()
        
        if not tokens:
            raise ValueError("No tokens available. Please complete OAuth flow first.")
        
        # Проверка истечения токена
        if self._is_token_expired(tokens):
            logger.info(
                "Access token expired, refreshing",
                extra={"operation": "bitrix.oauth.refresh", "result": "start"},
            )
            tokens = await self.refresh_access_token()
        
        return tokens["access_token"]
    
    def _save_tokens(self, tokens: Dict[str, Any]) -> None:
        """
        Сохранение токенов в файл
        
        Args:
            tokens: Словарь с токенами
        """
        # Добавление timestamp для отслеживания истечения
        tokens["saved_at"] = datetime.now().isoformat()
        
        with open(self.TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
        
        logger.info(
            "Tokens saved",
            extra={"operation": "bitrix.oauth.save", "result": "success"},
        )
    
    def _load_tokens(self) -> Optional[Dict[str, Any]]:
        """
        Загрузка токенов из файла
        
        Returns:
            Словарь с токенами или None
        """
        if not os.path.exists(self.TOKEN_FILE):
            return None
        
        try:
            with open(self.TOKEN_FILE, "r") as f:
                tokens = json.load(f)
            return tokens
        except Exception as e:
            logger.error(
                "Error loading tokens",
                extra={"operation": "bitrix.oauth.load", "result": "error"},
                exc_info=True,
            )
            return None
    
    def _is_token_expired(self, tokens: Dict[str, Any]) -> bool:
        """
        Проверка истечения токена
        
        Args:
            tokens: Словарь с токенами
            
        Returns:
            True если токен истек
        """
        if "saved_at" not in tokens or "expires_in" not in tokens:
            return True
        
        saved_at = datetime.fromisoformat(tokens["saved_at"])
        expires_in = int(tokens["expires_in"])
        
        # Обновляем токен за 5 минут до истечения
        expiry_time = saved_at + timedelta(seconds=expires_in - 300)
        
        return datetime.now() >= expiry_time


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
