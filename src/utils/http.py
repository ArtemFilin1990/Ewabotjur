"""
Shared HTTP client for efficient connection pooling
"""
import asyncio
import httpx
from typing import Optional

# Global client for connection reuse
_http_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()


async def get_http_client() -> httpx.AsyncClient:
    """
    Get the global HTTP client instance
    
    Returns:
        Shared httpx.AsyncClient instance
    """
    global _http_client
    if _http_client is None:
        async with _client_lock:
            # Double-check pattern to avoid race condition
            if _http_client is None:
                _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def close_http_client() -> None:
    """
    Close the global HTTP client
    """
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
