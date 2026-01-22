"""Pydantic schemas for Telegram updates."""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class TelegramUser(BaseModel):
    """Telegram user payload."""

    id: int = Field(..., ge=1)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramMessage(BaseModel):
    """Telegram message payload."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: int = Field(..., ge=1)
    date: int = Field(..., ge=0)
    text: Optional[str] = None
    from_user: Optional[TelegramUser] = Field(default=None, alias="from")
    sender_chat: Optional[dict] = None
    chat: Optional["TelegramChat"] = None
    document: Optional["TelegramDocument"] = None
    photo: Optional[List["TelegramPhoto"]] = None
    reply_to_message: Optional["TelegramMessage"] = None


class TelegramChat(BaseModel):
    """Telegram chat payload."""

    id: int = Field(..., ge=1)
    type: str


class TelegramDocument(BaseModel):
    """Telegram document payload."""

    file_id: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class TelegramPhoto(BaseModel):
    """Telegram photo payload."""

    file_id: str
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class TelegramCallbackQuery(BaseModel):
    """Telegram callback query payload."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_user: TelegramUser = Field(alias="from")
    data: Optional[str] = None
    message: Optional[TelegramMessage] = None


class TelegramUpdate(BaseModel):
    """Telegram update payload."""

    update_id: int = Field(..., ge=0)
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    callback_query: Optional[TelegramCallbackQuery] = None


TelegramMessage.model_rebuild()
