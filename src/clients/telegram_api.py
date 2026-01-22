"""Telegram Bot API client helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import io
import time

import httpx


@dataclass(frozen=True)
class TelegramFile:
    """Metadata for a Telegram file."""

    file_id: str
    file_unique_id: str
    file_size: Optional[int]
    file_path: str


class TelegramApiError(RuntimeError):
    """Raised when Telegram API request fails."""


class TelegramClient:
    """Simple Telegram Bot API client with retries."""

    def __init__(
        self,
        token: str,
        base_url: str,
        timeout_seconds: int,
        max_retries: int = 2,
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_retries = max_retries

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_payload: Optional[Dict[str, Any]] = None,
        data_payload: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self._base_url}/bot{self._token}/{endpoint}"
        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.request(
                        method,
                        url,
                        json=json_payload if files is None else None,
                        data=data_payload,
                        files=files,
                    )
                if response.status_code == 429:
                    retry_after = response.json().get("parameters", {}).get("retry_after", 1)
                    time.sleep(min(5, retry_after))
                    continue
                response.raise_for_status()
                payload = response.json()
                if not payload.get("ok"):
                    raise TelegramApiError(f"Telegram API error: {payload}")
                return payload
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                time.sleep(0.3 * (attempt + 1))
        raise TelegramApiError(f"Telegram API request failed: {last_error}")

    def send_message(self, chat_id: int, text: str) -> None:
        """Send a text message to a chat."""

        self._request(
            "POST",
            "sendMessage",
            json_payload={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
        )

    def send_document(self, chat_id: int, filename: str, content: bytes, caption: str | None = None) -> None:
        """Send a document to a chat."""

        files = {"document": (filename, io.BytesIO(content))}
        payload = {"chat_id": str(chat_id)}
        if caption:
            payload["caption"] = caption
        self._request("POST", "sendDocument", data_payload=payload, files=files)

    def get_file(self, file_id: str) -> TelegramFile:
        """Fetch file metadata for a Telegram file id."""

        payload = self._request(
            "POST",
            "getFile",
            json_payload={"file_id": file_id},
        )
        result = payload.get("result", {})
        return TelegramFile(
            file_id=result.get("file_id", file_id),
            file_unique_id=result.get("file_unique_id", ""),
            file_size=result.get("file_size"),
            file_path=result.get("file_path", ""),
        )

    def download_file(self, file_path: str) -> bytes:
        """Download file bytes from Telegram."""

        url = f"{self._base_url}/file/bot{self._token}/{file_path}"
        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.HTTPError as exc:
                last_error = exc
                time.sleep(0.3 * (attempt + 1))
        raise TelegramApiError(f"Telegram file download failed: {last_error}")
