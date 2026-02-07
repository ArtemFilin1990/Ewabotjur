"""
Конфигурация приложения Ewabotjur
Все настройки загружаются из переменных окружения
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения"""
    
    # Общие настройки
    port: int = int(os.getenv("PORT", "3000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    app_url: str = os.getenv("APP_URL", "http://localhost:3000")
    
    # Telegram Bot
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_webhook_secret: str = os.getenv("TG_WEBHOOK_SECRET", "")
    
    # DaData API
    dadata_api_key: str = os.getenv("DADATA_API_KEY", "")
    dadata_secret_key: str = os.getenv("DADATA_SECRET_KEY", "")
    
    # OpenAI GPT
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Bitrix24 OAuth
    bitrix_domain: str = os.getenv("BITRIX_DOMAIN", "")
    bitrix_client_id: str = os.getenv("BITRIX_CLIENT_ID", "")
    bitrix_client_secret: str = os.getenv("BITRIX_CLIENT_SECRET", "")
    bitrix_redirect_url: str = os.getenv("BITRIX_REDIRECT_URL", "")
    
    # MCP (опционально)
    use_mcp: bool = os.getenv("USE_MCP", "false").lower() == "true"
    mcp_server_url: Optional[str] = os.getenv("MCP_SERVER_URL")
    mcp_api_key: Optional[str] = os.getenv("MCP_API_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
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
