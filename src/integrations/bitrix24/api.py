"""
Bitrix24 API интеграция для отправки сообщений через imbot
"""
import logging
import httpx
from typing import Dict, Any, Optional

from src.config import settings
from src.integrations.bitrix24.oauth import get_access_token
from src.utils.http import get_http_client

logger = logging.getLogger(__name__)


class BitrixAPIClient:
    """Клиент для работы с Bitrix24 REST API"""
    
    def __init__(self):
        self.domain = settings.bitrix_domain
    
    async def send_message(
        self,
        dialog_id: str,
        message: str,
        bot_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Отправка сообщения через imbot.message.add
        
        Args:
            dialog_id: ID диалога (chat ID)
            message: Текст сообщения
            bot_id: ID бота (опционально)
            
        Returns:
            Ответ API
        """
        # Получение валидного токена (с автообновлением)
        access_token = await get_access_token()
        
        # URL для REST API
        url = f"{self.domain}/rest/imbot.message.add"
        
        # Параметры запроса
        params = {
            "auth": access_token,
            "DIALOG_ID": dialog_id,
            "MESSAGE": message
        }
        
        if bot_id:
            params["BOT_ID"] = bot_id
        
        try:
            client = get_http_client()
            response = await client.post(url, json=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                logger.error(
                    "Bitrix24 API error",
                    extra={
                        "operation": "bitrix.message.send",
                        "result": "error",
                        "dialog_id": dialog_id,
                        "error": data.get("error"),
                    },
                )
                raise Exception(f"Bitrix24 API error: {data['error_description']}")

            logger.info(
                "Message sent to Bitrix dialog",
                extra={"operation": "bitrix.message.send", "result": "success", "dialog_id": dialog_id},
            )
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error sending Bitrix message",
                extra={
                    "operation": "bitrix.message.send",
                    "result": "error",
                    "status_code": e.response.status_code,
                },
            )
            raise
        except Exception as e:
            logger.error(
                "Error sending Bitrix message",
                extra={"operation": "bitrix.message.send", "result": "error"},
                exc_info=True,
            )
            raise
    
    async def call_method(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Универсальный вызов метода Bitrix24 REST API
        
        Args:
            method: Название метода (например, "imbot.message.add")
            params: Параметры метода
            
        Returns:
            Ответ API
        """
        # Получение валидного токена
        access_token = await get_access_token()
        
        url = f"{self.domain}/rest/{method}"
        
        request_params = params or {}
        request_params["auth"] = access_token
        
        try:
            client = get_http_client()
            response = await client.post(url, json=request_params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                logger.error(
                    "Bitrix24 API error",
                    extra={
                        "operation": "bitrix.api.call",
                        "result": "error",
                        "method": method,
                        "error": data.get("error"),
                    },
                )
                raise Exception(f"Bitrix24 API error: {data['error_description']}")
            
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error calling Bitrix API",
                extra={
                    "operation": "bitrix.api.call",
                    "result": "error",
                    "method": method,
                    "status_code": e.response.status_code,
                },
            )
            raise
        except Exception as e:
            logger.error(
                "Error calling Bitrix API",
                extra={"operation": "bitrix.api.call", "result": "error", "method": method},
                exc_info=True,
            )
            raise


# Глобальный экземпляр клиента
bitrix_client = BitrixAPIClient()
