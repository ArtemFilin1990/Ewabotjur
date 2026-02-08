"""
Конфигурация приложения Ewabotjur
Все настройки загружаются из переменных окружения
"""
from typing import Optional
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Общие настройки
    port: int = Field(default=3000, validation_alias="PORT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    app_url: str = Field(default="http://localhost:3000", validation_alias="APP_URL")
    
    # Telegram Bot
    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    tg_webhook_secret: str = Field(
        default="",
        validation_alias=AliasChoices("TELEGRAM_WEBHOOK_SECRET", "TG_WEBHOOK_SECRET"),
    )
    
    # DaData API
    dadata_api_key: str = Field(default="", validation_alias="DADATA_API_KEY")
    dadata_secret_key: str = Field(default="", validation_alias="DADATA_SECRET_KEY")
    
    # OpenAI GPT
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", validation_alias="OPENAI_MODEL")
    
    # Bitrix24 OAuth
    bitrix_domain: str = Field(default="", validation_alias="BITRIX_DOMAIN")
    bitrix_client_id: str = Field(default="", validation_alias="BITRIX_CLIENT_ID")
    bitrix_client_secret: str = Field(default="", validation_alias="BITRIX_CLIENT_SECRET")
    bitrix_redirect_url: str = Field(default="", validation_alias="BITRIX_REDIRECT_URL")

    # Database
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    
    # MCP (опционально)
    use_mcp: bool = Field(default=False, validation_alias="USE_MCP")
    mcp_server_url: Optional[str] = Field(default=None, validation_alias="MCP_SERVER_URL")
    mcp_api_key: Optional[str] = Field(default=None, validation_alias="MCP_API_KEY")
    
    def validate_required(self) -> list[str]:
        """Проверяет наличие обязательных переменных"""
        missing = []
        
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.tg_webhook_secret:
            missing.append("TG_WEBHOOK_SECRET")
        if not self.dadata_api_key:
            missing.append("DADATA_API_KEY")
        if not self.dadata_secret_key:
            missing.append("DADATA_SECRET_KEY")
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.bitrix_domain:
            missing.append("BITRIX_DOMAIN")
        if not self.bitrix_client_id:
            missing.append("BITRIX_CLIENT_ID")
        if not self.bitrix_client_secret:
            missing.append("BITRIX_CLIENT_SECRET")
        if not self.bitrix_redirect_url:
            missing.append("BITRIX_REDIRECT_URL")
        if not self.database_url:
            missing.append("DATABASE_URL")
        
        return missing
    
    @property
    def telegram_webhook_url(self) -> str:
        """Полный URL для Telegram webhook"""
        return f"{self.app_url}/webhook/telegram/{self.tg_webhook_secret}"
    
    @property
    def bitrix_callback_url(self) -> str:
        """URL для OAuth callback Bitrix24"""
        return f"{self.app_url}/oauth/bitrix/callback"


# Глобальный экземпляр настроек
settings = Settings()
