"""
Главная точка входа FastAPI приложения Ewabotjur
Обрабатывает webhook от Telegram и Bitrix24
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

from src.config import settings
from src.handlers.telegram_handler import handle_telegram_update
from src.handlers.bitrix_handler import handle_bitrix_event
from src.integrations.bitrix24.oauth import handle_oauth_callback, initiate_oauth

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events для приложения"""
    # Startup
    logger.info("Starting Ewabotjur application")
    logger.info(f"App URL: {settings.app_url}")
    logger.info(f"Port: {settings.port}")
    
    # Проверка обязательных переменных
    missing = settings.validate_required()
    if missing:
        logger.warning(f"Missing environment variables: {', '.join(missing)}")
        logger.warning("Some features may not work correctly")
    else:
        logger.info("All required environment variables are set")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ewabotjur application")


# Создание FastAPI приложения
app = FastAPI(
    title="Ewabotjur",
    description="Telegram + Bitrix24 bot для анализа контрагентов по ИНН",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "Ewabotjur",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check для мониторинга"""
    return {
        "status": "healthy",
        "has_telegram_token": bool(settings.telegram_bot_token),
        "has_dadata_key": bool(settings.dadata_api_key),
        "has_openai_key": bool(settings.openai_api_key),
        "has_bitrix_config": bool(settings.bitrix_domain and settings.bitrix_client_id)
    }


@app.post("/webhook/telegram/{secret}")
async def telegram_webhook(secret: str, request: Request):
    """
    Webhook endpoint для Telegram
    URL: POST /webhook/telegram/{TG_WEBHOOK_SECRET}
    """
    # Проверка секретного ключа
    if secret != settings.tg_webhook_secret:
        logger.warning(f"Invalid webhook secret attempt from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook secret"
        )
    
    try:
        # Получение тела запроса
        update_data = await request.json()
        logger.info(f"Received Telegram update: {update_data.get('update_id', 'unknown')}")
        
        # Обработка update
        await handle_telegram_update(update_data)
        
        return JSONResponse({"ok": True})
    
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}", exc_info=True)
        # Telegram ожидает 200 OK даже при ошибках
        return JSONResponse({"ok": False, "error": str(e)})


@app.post("/webhook/bitrix")
async def bitrix_webhook(request: Request):
    """
    Webhook endpoint для Bitrix24 (imbot events)
    URL: POST /webhook/bitrix
    """
    try:
        # Получение тела запроса
        event_data = await request.form()
        event_dict = dict(event_data)
        
        logger.info(f"Received Bitrix event: {event_dict.get('event', 'unknown')}")
        
        # Обработка события
        await handle_bitrix_event(event_dict)
        
        return JSONResponse({"success": True})
    
    except Exception as e:
        logger.error(f"Error processing Bitrix webhook: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)})


@app.get("/oauth/bitrix/start")
async def start_bitrix_oauth():
    """
    Инициация OAuth процесса для Bitrix24
    Перенаправляет пользователя на страницу авторизации Bitrix24
    """
    try:
        auth_url = initiate_oauth()
        return {
            "auth_url": auth_url,
            "message": "Перейдите по ссылке для авторизации в Bitrix24"
        }
    except Exception as e:
        logger.error(f"Error initiating OAuth: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth initiation failed: {str(e)}"
        )


@app.get("/oauth/bitrix/callback")
async def bitrix_oauth_callback(code: str = None, error: str = None):
    """
    Callback endpoint для OAuth Bitrix24
    URL: GET /oauth/bitrix/callback?code=...
    """
    if error:
        logger.error(f"OAuth error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    try:
        # Обмен кода на токены
        token_data = await handle_oauth_callback(code)
        
        return {
            "success": True,
            "message": "Bitrix24 OAuth успешно завершен",
            "expires_in": token_data.get("expires_in"),
            "has_refresh_token": "refresh_token" in token_data
        }
    
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Запуск приложения
    # ВАЖНО: слушаем порт из переменной окружения PORT
    port = settings.port
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        log_level=settings.log_level.lower()
    )
