"""Bitrix24 OAuth authentication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import httpx
import json
import time

from src.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class BitrixTokens:
    """Bitrix24 OAuth tokens."""
    
    access_token: str
    refresh_token: str
    expires_at: float  # Unix timestamp
    domain: str


class BitrixOAuthError(RuntimeError):
    """Raised for Bitrix24 OAuth errors."""


class BitrixOAuthClient:
    """Bitrix24 OAuth client for managing authentication."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        domain: str,
    ):
        """
        Initialize OAuth client.
        
        Args:
            client_id: Bitrix24 application client ID
            client_secret: Bitrix24 application client secret
            redirect_uri: OAuth callback URL
            domain: Bitrix24 portal domain (e.g., https://xxx.bitrix24.ru)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.domain = domain.rstrip("/")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
        
        Returns:
            Authorization URL for redirecting user
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
        }
        if state:
            params["state"] = state
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.domain}/oauth/authorize/?{query}"
    
    async def exchange_code(self, code: str, timeout_seconds: float = 15.0) -> BitrixTokens:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            timeout_seconds: Request timeout
        
        Returns:
            BitrixTokens with access and refresh tokens
        
        Raises:
            BitrixOAuthError: If token exchange fails
        """
        url = f"{self.domain}/oauth/token/"
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        timeout = httpx.Timeout(timeout_seconds)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            expires_in = data.get("expires_in", 3600)
            
            if not access_token or not refresh_token:
                raise BitrixOAuthError("Invalid token response from Bitrix24")
            
            logger.info(
                "bitrix oauth token obtained",
                extra={"module": "bitrix_oauth", "status": "success"},
            )
            
            return BitrixTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=time.time() + expires_in,
                domain=self.domain,
            )
            
        except httpx.HTTPStatusError as exc:
            logger.error(
                "bitrix oauth error",
                extra={
                    "module": "bitrix_oauth",
                    "status": "error",
                    "status_code": exc.response.status_code,
                },
            )
            raise BitrixOAuthError(f"Token exchange failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error(
                "bitrix oauth request error",
                extra={
                    "module": "bitrix_oauth",
                    "status": "error",
                    "error_type": type(exc).__name__,
                },
            )
            raise BitrixOAuthError("Failed to connect to Bitrix24") from exc
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        timeout_seconds: float = 15.0,
    ) -> BitrixTokens:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            timeout_seconds: Request timeout
        
        Returns:
            New BitrixTokens
        
        Raises:
            BitrixOAuthError: If token refresh fails
        """
        url = f"{self.domain}/oauth/token/"
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        
        timeout = httpx.Timeout(timeout_seconds)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")
            expires_in = data.get("expires_in", 3600)
            
            if not access_token or not new_refresh_token:
                raise BitrixOAuthError("Invalid refresh token response")
            
            logger.info(
                "bitrix token refreshed",
                extra={"module": "bitrix_oauth", "status": "success"},
            )
            
            return BitrixTokens(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_at=time.time() + expires_in,
                domain=self.domain,
            )
            
        except httpx.HTTPStatusError as exc:
            logger.error(
                "bitrix token refresh error",
                extra={
                    "module": "bitrix_oauth",
                    "status": "error",
                    "status_code": exc.response.status_code,
                },
            )
            raise BitrixOAuthError(f"Token refresh failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error(
                "bitrix token refresh request error",
                extra={
                    "module": "bitrix_oauth",
                    "status": "error",
                    "error_type": type(exc).__name__,
                },
            )
            raise BitrixOAuthError("Failed to connect to Bitrix24") from exc
    
    def is_token_expired(self, tokens: BitrixTokens, buffer_seconds: int = 60) -> bool:
        """
        Check if access token is expired or will expire soon.
        
        Args:
            tokens: BitrixTokens to check
            buffer_seconds: Consider token expired if it expires within this buffer
        
        Returns:
            True if token is expired or will expire soon
        """
        return time.time() >= (tokens.expires_at - buffer_seconds)
