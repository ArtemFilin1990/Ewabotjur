"""Telegram Bot API client helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import io

import httpx


@dataclass(frozen=True)
class TelegramFile:
    """Metadata for a Telegram file."""

    file_path: str
    file_size: Optional[int] = None


class TelegramClient:
    """Client for Telegram Bot API."""

    def __init__(self, bot_token: str, timeout_seconds: int) -> None:
        self._bot_token = bot_token
        self._timeout_seconds = timeout_seconds
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._file_base_url = f"https://api.telegram.org/file/bot{bot_token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
    ) -> None:
        """Send a message to a Telegram chat."""

        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(f"{self._base_url}/sendMessage", json=payload)
            response.raise_for_status()

    async def send_document(
        self,
        chat_id: int,
        filename: str,
        content: bytes,
        caption: Optional[str] = None,
    ) -> None:
        """Send a document to a Telegram chat."""

        data: dict[str, Any] = {"chat_id": str(chat_id)}
        if caption:
            data["caption"] = caption
        files = {"document": (filename, io.BytesIO(content))}
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/sendDocument", data=data, files=files
            )
            response.raise_for_status()

    async def get_file(self, file_id: str) -> TelegramFile:
        """Fetch file metadata for a Telegram file."""

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/getFile", json={"file_id": file_id}
            )
            response.raise_for_status()
            payload = response.json()
        result = payload.get("result", {})
        return TelegramFile(
            file_path=result.get("file_path", ""),
            file_size=result.get("file_size"),
        )

    async def download_file(self, file_path: str) -> bytes:
        """Download a Telegram file by path."""

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(f"{self._file_base_url}/{file_path}")
            response.raise_for_status()
            return response.content
