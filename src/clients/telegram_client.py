"""Telegram Bot API client helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import httpx


@dataclass(frozen=True)
class TelegramFile:
    """Metadata about a Telegram file."""

    file_id: str
    file_path: str


class TelegramClient:
    """HTTP client for interacting with Telegram Bot API."""

    def __init__(self, token: str, base_url: str, timeout_seconds: int) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    @property
    def api_base(self) -> str:
        """Return API base URL."""

        return f"{self._base_url}/bot{self._token}"

    @property
    def file_base(self) -> str:
        """Return file download base URL."""

        return f"{self._base_url}/file/bot{self._token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """Send a message to a Telegram chat."""

        payload = {"chat_id": chat_id, "text": text}
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        await self._post("sendMessage", payload)

    async def send_document(
        self,
        chat_id: int,
        filename: str,
        content: bytes,
        caption: Optional[str] = None,
    ) -> None:
        """Send a document to a Telegram chat."""

        data = {"chat_id": str(chat_id)}
        if caption:
            data["caption"] = caption
        files = {"document": (filename, content)}
        await self._post("sendDocument", data=data, files=files)

    async def get_file(self, file_id: str) -> TelegramFile:
        """Retrieve file metadata from Telegram."""

        payload = {"file_id": file_id}
        response = await self._post("getFile", payload)
        file_path = response["result"]["file_path"]
        return TelegramFile(file_id=file_id, file_path=file_path)

    async def download_file(self, file_path: str) -> bytes:
        """Download file contents from Telegram."""

        url = f"{self.file_base}/{file_path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def _post(
        self,
        method: str,
        payload: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
    ) -> dict:
        url = f"{self.api_base}/{method}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, data=data, files=files)
            response.raise_for_status()
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError(f"Telegram API error: {body}")
            return body
