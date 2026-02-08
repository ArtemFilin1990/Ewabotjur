"""
Главная точка входа FastAPI приложения Ewabotjur
Обрабатывает webhook от Telegram и Bitrix24
"""
import logging
import time
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

from src.config import settings
from src.handlers.telegram_handler import handle_telegram_update
from src.handlers.bitrix_handler import handle_bitrix_event
from src.integrations.bitrix24.oauth import handle_oauth_callback, initiate_oauth
from src.utils.logging import configure_logging, reset_request_id, set_request_id

# Настройка логирования
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events для приложения"""
    # Startup
    logger.info("Starting Ewabotjur application", extra={"operation": "startup", "result": "success"})
    logger.info(
        "App URL configured",
        extra={"operation": "startup", "result": "success", "app_url": settings.app_url},
    )
    logger.info(
        "Port configured",
        extra={"operation": "startup", "result": "success", "port": settings.port},
    )
    
    # Проверка обязательных переменных
    missing = settings.validate_required()
    if missing:
        logger.warning(
            "Missing environment variables",
            extra={"operation": "config.validation", "result": "warning", "missing": missing},
        )
        logger.warning(
            "Some features may not work correctly",
            extra={"operation": "config.validation", "result": "warning"},
        )
    else:
        logger.info(
            "All required environment variables are set",
            extra={"operation": "config.validation", "result": "success"},
        )
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ewabotjur application", extra={"operation": "shutdown", "result": "success"})


# Создание FastAPI приложения
app = FastAPI(
    title="Ewabotjur",
    description="Telegram + Bitrix24 bot для анализа контрагентов по ИНН",
    version="1.0.0",
    lifespan=lifespan
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Middleware для request_id и метрик времени."""
    incoming_request_id = request.headers.get("X-Request-ID")
    request_id = incoming_request_id or str(uuid4())
    token = set_request_id(request_id)
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Request processed",
            extra={
                "operation": "http_request",
                "result": "success",
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(
            "Request failed",
            extra={
                "operation": "http_request",
                "result": "error",
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
            exc_info=True,
        )
        raise
    finally:
        reset_request_id(token)


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
        "status": "ok",
        "checks": {
            "has_telegram_token": bool(settings.telegram_bot_token),
            "has_dadata_key": bool(settings.dadata_api_key),
            "has_openai_key": bool(settings.openai_api_key),
            "has_bitrix_config": bool(settings.bitrix_domain and settings.bitrix_client_id),
        },
    }


@app.post("/webhook/telegram/{secret}")
async def telegram_webhook(secret: str, request: Request):
    """
    Webhook endpoint для Telegram
    URL: POST /webhook/telegram/{TG_WEBHOOK_SECRET}
    """
    # Проверка секретного ключа
    if secret != settings.tg_webhook_secret:
        logger.warning(
            "Invalid webhook secret attempt",
            extra={"operation": "telegram.webhook", "result": "forbidden"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook secret"
        )
    
    try:
        # Получение тела запроса
        update_data = await request.json()
        logger.info(
            "Received Telegram update",
            extra={
                "operation": "telegram.webhook",
                "result": "success",
                "update_id": update_data.get("update_id", "unknown"),
            },
        )
        
        # Обработка update
        await handle_telegram_update(update_data)
        
        return JSONResponse({"ok": True})
    
    except Exception as e:
        logger.error(
            "Error processing Telegram webhook",
            extra={"operation": "telegram.webhook", "result": "error"},
            exc_info=True,
        )
        # Telegram ожидает 200 OK даже при ошибках
        return JSONResponse({"ok": False, "error": str(e)})


async def _parse_bitrix_payload(request: Request) -> dict:
    """Получает payload Bitrix24 из form-data или JSON."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        if isinstance(payload, dict):
            return payload
        return {"payload": payload}

    event_data = await request.form()
    return dict(event_data)


async def _handle_bitrix_request(request: Request) -> JSONResponse:
    """
    Webhook endpoint для Bitrix24 (imbot events)
    URL: POST /webhook/bitrix
    """
    try:
        # Получение тела запроса
        event_dict = await _parse_bitrix_payload(request)
        
        logger.info(
            "Received Bitrix event",
            extra={
                "operation": "bitrix.webhook",
                "result": "success",
                "event": event_dict.get("event", "unknown"),
            },
        )
        
        # Обработка события
        await handle_bitrix_event(event_dict)
        
        return JSONResponse({"success": True})
    
    except Exception as e:
        logger.error(
            "Error processing Bitrix webhook",
            extra={"operation": "bitrix.webhook", "result": "error"},
            exc_info=True,
        )
        return JSONResponse({"success": False, "error": str(e)})


@app.post("/webhook/bitrix")
async def bitrix_webhook(request: Request):
    """
    Webhook endpoint для Bitrix24 (imbot events)
    URL: POST /webhook/bitrix
    """
    return await _handle_bitrix_request(request)


@app.post("/bitrix/event")
async def bitrix_event(request: Request):
    """
    Альтернативный webhook endpoint для Bitrix24
    URL: POST /bitrix/event
    """
    return await _handle_bitrix_request(request)


async def _start_bitrix_oauth() -> dict:
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
        logger.error(
            "Error initiating OAuth",
            extra={"operation": "bitrix.oauth.start", "result": "error"},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth initiation failed: {str(e)}"
        )


@app.get("/oauth/bitrix")
async def start_bitrix_oauth():
    """Инициация OAuth процесса для Bitrix24 (короткий маршрут)."""
    return await _start_bitrix_oauth()


@app.get("/oauth/bitrix/start")
async def start_bitrix_oauth_legacy():
    """Инициация OAuth процесса для Bitrix24 (legacy маршрут)."""
    return await _start_bitrix_oauth()


@app.get("/oauth/bitrix/callback")
async def bitrix_oauth_callback(code: str = None, error: str = None):
    """
    Callback endpoint для OAuth Bitrix24
    URL: GET /oauth/bitrix/callback?code=...
    """
    if error:
        logger.error(
            "OAuth error",
            extra={"operation": "bitrix.oauth.callback", "result": "error"},
        )
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
        logger.error(
            "Error handling OAuth callback",
            extra={"operation": "bitrix.oauth.callback", "result": "error"},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Запуск приложения
    # ВАЖНО: слушаем порт из переменной окружения PORT
    port = settings.port
    logger.info(
        "Starting server",
        extra={"operation": "startup", "result": "success", "port": port},
    )
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        log_level=settings.log_level.lower()
    )
