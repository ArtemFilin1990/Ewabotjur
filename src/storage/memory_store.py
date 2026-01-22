"""Simple JSON-backed memory store for per-chat context."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional


@dataclass
class ChatMemory:
    """Stored memory for a single chat."""

    chat_id: int
    last_document_text: Optional[str] = None
    last_command: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class MemoryStore:
    """Thread-safe JSON memory store keyed by chat_id."""

    def __init__(self, path: str):
        self._path = Path(path)
        self._lock = Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_all(self, payload: Dict[str, Any]) -> None:
        tmp_path = self._path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self._path)

    def get(self, chat_id: int) -> ChatMemory:
        """Return memory for a chat, creating defaults if missing."""

        with self._lock:
            data = self._read_all()
            item = data.get(str(chat_id))
            if isinstance(item, dict):
                return ChatMemory(**item)
            return ChatMemory(chat_id=chat_id)

    def upsert(self, memory: ChatMemory) -> None:
        """Persist memory for a chat."""

        memory.updated_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            data = self._read_all()
            data[str(memory.chat_id)] = asdict(memory)
            self._write_all(data)

    def clear(self, chat_id: int) -> None:
        """Delete memory for a chat."""

        with self._lock:
            data = self._read_all()
            data.pop(str(chat_id), None)
            self._write_all(data)

    def reset_task(self, chat_id: int) -> None:
        """Reset task-specific memory while keeping preferences."""

        with self._lock:
            data = self._read_all()
            item = data.get(str(chat_id), {})
            if not isinstance(item, dict):
                item = {}
            updated = ChatMemory(
                chat_id=chat_id,
                last_document_text=None,
                last_command=None,
                user_preferences=item.get("user_preferences", {}),
            )
            data[str(chat_id)] = asdict(updated)
            self._write_all(data)
