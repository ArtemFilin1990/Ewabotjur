"""Централизованная конфигурация приложения."""
from __future__ import annotations

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    port: int = Field(default=3000, validation_alias="PORT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    app_url: str = Field(default="http://localhost:3000", validation_alias="APP_URL")

    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    tg_webhook_secret: str = Field(default="", validation_alias=AliasChoices("TELEGRAM_WEBHOOK_SECRET", "TG_WEBHOOK_SECRET"))

    dadata_api_key: str = Field(default="", validation_alias="DADATA_API_KEY")
    dadata_secret_key: str = Field(default="", validation_alias="DADATA_SECRET_KEY")

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", validation_alias="OPENAI_MODEL")

    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    http_timeout_seconds: float = Field(default=10.0, validation_alias="HTTP_TIMEOUT_SECONDS")

    bitrix_domain: str = Field(default="", validation_alias="BITRIX_DOMAIN")
    bitrix_client_id: str = Field(default="", validation_alias="BITRIX_CLIENT_ID")
    bitrix_client_secret: str = Field(default="", validation_alias="BITRIX_CLIENT_SECRET")
    bitrix_redirect_url: str = Field(default="", validation_alias="BITRIX_REDIRECT_URL")

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        candidate = value.upper()
        if candidate not in allowed:
            return "INFO"
        return candidate

    @field_validator("http_timeout_seconds")
    @classmethod
    def _validate_timeout(cls, value: float) -> float:
        return max(1.0, min(value, 60.0))

    def validate_required(self) -> list[str]:
        """Возвращает список отсутствующих обязательных env-переменных."""
        required = {
            "TELEGRAM_BOT_TOKEN": self.telegram_bot_token,
            "TG_WEBHOOK_SECRET": self.tg_webhook_secret,
            "DADATA_API_KEY": self.dadata_api_key,
            "DADATA_SECRET_KEY": self.dadata_secret_key,
            "DATABASE_URL": self.database_url,
            "BITRIX_DOMAIN": self.bitrix_domain,
            "BITRIX_CLIENT_ID": self.bitrix_client_id,
            "BITRIX_CLIENT_SECRET": self.bitrix_client_secret,
            "BITRIX_REDIRECT_URL": self.bitrix_redirect_url,
        }
        return [name for name, value in required.items() if not value]

    @property
    def telegram_webhook_url(self) -> str:
        """Полный URL webhook Telegram."""
        return f"{self.app_url}/webhook/telegram/{self.tg_webhook_secret}"


settings = Settings()
