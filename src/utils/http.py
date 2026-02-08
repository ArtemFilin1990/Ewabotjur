"""
Shared HTTP client for efficient connection pooling
"""
import httpx
from typing import Optional

# Глобальный клиент для переиспользования соединений
_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """
    Получить глобальный экземпляр HTTP клиента
    
    Returns:
        Shared httpx.AsyncClient instance
    """
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def close_http_client() -> None:
    """
    Закрыть глобальный HTTP клиент
    """
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
