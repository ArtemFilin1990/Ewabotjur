"""Bitrix24 REST API client."""

from __future__ import annotations

from typing import Any, Optional
import httpx

from src.integrations.bitrix24.oauth import BitrixTokens
from src.logging_config import get_logger


logger = get_logger(__name__)


class BitrixAPIError(RuntimeError):
    """Raised for Bitrix24 API errors."""


class BitrixAPIClient:
    """Bitrix24 REST API client for imbot messaging."""
    
    def __init__(
        self,
        tokens: BitrixTokens,
        timeout_seconds: float = 15.0,
    ):
        """
        Initialize API client.
        
        Args:
            tokens: OAuth tokens for authentication
            timeout_seconds: Default request timeout
        """
        self.tokens = tokens
        self.timeout_seconds = timeout_seconds
        self.base_url = f"{tokens.domain}/rest"
    
    async def send_message(
        self,
        dialog_id: str,
        message: str,
    ) -> dict[str, Any]:
        """
        Send message to Bitrix24 chat using imbot.message.add.
        
        Args:
            dialog_id: Chat/dialog ID (e.g., "chatXXX" or user ID)
            message: Message text to send
        
        Returns:
            API response data
        
        Raises:
            BitrixAPIError: If API request fails
        """
        method = "imbot.message.add"
        params = {
            "DIALOG_ID": dialog_id,
            "MESSAGE": message,
        }
        
        return await self._call_method(method, params)
    
    async def _call_method(
        self,
        method: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Call Bitrix24 REST API method.
        
        Args:
            method: API method name (e.g., "imbot.message.add")
            params: Method parameters
        
        Returns:
            API response result
        
        Raises:
            BitrixAPIError: If API call fails
        """
        url = f"{self.base_url}/{method}"
        
        payload = params or {}
        payload["auth"] = self.tokens.access_token
        
        timeout = httpx.Timeout(self.timeout_seconds)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                error_code = data.get("error")
                error_description = data.get("error_description", "Unknown error")
                logger.error(
                    "bitrix api error",
                    extra={
                        "module": "bitrix_api",
                        "status": "error",
                        "error_code": error_code,
                        "error_description": error_description,
                    },
                )
                raise BitrixAPIError(f"Bitrix24 API error: {error_code} - {error_description}")
            
            result = data.get("result")
            if result is None:
                logger.warning(
                    "bitrix api returned no result",
                    extra={"module": "bitrix_api", "status": "warning"},
                )
            
            logger.info(
                "bitrix api call successful",
                extra={
                    "module": "bitrix_api",
                    "status": "success",
                    "method": method,
                },
            )
            
            return data
            
        except httpx.HTTPStatusError as exc:
            logger.error(
                "bitrix api http error",
                extra={
                    "module": "bitrix_api",
                    "status": "error",
                    "status_code": exc.response.status_code,
                },
            )
            raise BitrixAPIError(f"HTTP error {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error(
                "bitrix api request error",
                extra={
                    "module": "bitrix_api",
                    "status": "error",
                    "error_type": type(exc).__name__,
                },
            )
            raise BitrixAPIError("Failed to connect to Bitrix24") from exc
