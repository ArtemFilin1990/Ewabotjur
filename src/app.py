"""FastAPI application setup."""

from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.bot.schemas import TelegramUpdate
from src.handlers.telegram_handler import process_update
from src.handlers.bitrix_handler import process_bitrix_event
from src.config import AppConfig, load_config
from src.logging_config import configure_logging, get_logger


config = load_config()
configure_logging(config.log_level)
logger = get_logger(__name__)

app = FastAPI(title=config.app_name)


def _get_request_id(request: Request) -> str:
    header_name = config.request_id_header
    return request.headers.get(header_name, str(uuid4()))


async def _enforce_body_size(request: Request) -> None:
    content_length = request.headers.get("content-length")
    if content_length is None:
        return
    try:
        size = int(content_length)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid Content-Length header") from exc
    if size > config.max_request_body_bytes:
        raise HTTPException(status_code=413, detail="Request payload too large")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = _get_request_id(request)
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[config.request_id_header] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    logger.warning(
        "request validation error",
        extra={"request_id": request_id, "status_code": 422},
    )
    return JSONResponse(
        status_code=422,
        content={"status": "invalid_request", "request_id": request_id},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""

    return {
        "status": "ok",
        "app": config.app_name,
        "environment": config.environment,
    }


@app.post("/webhook/telegram/{secret}")
async def telegram_webhook(
    secret: str,
    update: TelegramUpdate,
    request: Request,
    _: None = Depends(_enforce_body_size),
):
    """
    Telegram webhook endpoint.
    
    URL format: POST /webhook/telegram/<TG_WEBHOOK_SECRET>
    
    Set webhook with:
    curl -s "https://api.telegram.org/bot<TOKEN>/setWebhook" \\
      -d "url=https://<YOUR_DOMAIN>/webhook/telegram/<SECRET>"
    """
    request_id = request.state.request_id
    
    # Validate webhook secret
    if not config.tg_webhook_secret:
        logger.error(
            "telegram webhook secret not configured",
            extra={"request_id": request_id, "status_code": 500},
        )
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    if secret != config.tg_webhook_secret:
        logger.warning(
            "telegram webhook rejected: invalid secret",
            extra={"request_id": request_id, "status_code": 403},
        )
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    try:
        await process_update(update, config, logger, request_id)
    except Exception:
        logger.exception(
            "telegram update processing failed",
            extra={"request_id": request_id, "status_code": 500},
        )
    
    return JSONResponse(
        status_code=200, content={"status": "accepted", "request_id": request_id}
    )


@app.post("/webhook/bitrix")
async def bitrix_webhook(
    request: Request,
    _: None = Depends(_enforce_body_size),
):
    """
    Bitrix24 webhook endpoint for incoming messages.
    
    This endpoint receives events from Bitrix24 imbot.
    Configure this URL in your Bitrix24 application settings.
    """
    request_id = request.state.request_id
    
    try:
        # Parse Bitrix24 webhook payload
        data = await request.json()
        
        logger.info(
            "bitrix webhook received",
            extra={
                "request_id": request_id,
                "event": data.get("event"),
                "status_code": 200,
            },
        )
        
        # Process Bitrix24 event
        await process_bitrix_event(data, config, logger, request_id)
        
        return JSONResponse(
            status_code=200,
            content={"status": "accepted", "request_id": request_id},
        )
        
    except Exception:
        logger.exception(
            "bitrix webhook processing failed",
            extra={"request_id": request_id, "status_code": 500},
        )
        return JSONResponse(
            status_code=200,  # Return 200 even on error to avoid retries
            content={"status": "error", "request_id": request_id},
        )


@app.get("/oauth/bitrix/callback")
async def bitrix_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(None, description="State parameter"),
    request: Request = None,
):
    """
    Bitrix24 OAuth callback endpoint.
    
    This endpoint receives the authorization code after user authorizes the app.
    Configure this URL as the redirect_uri in Bitrix24 application settings.
    """
    request_id = request.state.request_id
    
    logger.info(
        "bitrix oauth callback received",
        extra={"request_id": request_id, "has_code": bool(code)},
    )
    
    try:
        from src.integrations.bitrix24 import BitrixOAuthClient
        from src.storage.bitrix_token_store import BitrixTokenStore
        
        oauth_client = BitrixOAuthClient(
            client_id=config.bitrix_client_id,
            client_secret=config.bitrix_client_secret,
            redirect_uri=config.bitrix_redirect_url,
            domain=config.bitrix_domain,
        )
        
        tokens = await oauth_client.exchange_code(code)
        
        # Store tokens securely
        token_store = BitrixTokenStore(config.memory_store_path)
        await token_store.save_tokens(tokens)
        
        logger.info(
            "bitrix oauth token obtained and stored",
            extra={
                "request_id": request_id,
                "expires_at": tokens.expires_at,
            },
        )
        
        return {
            "status": "success",
            "message": "Authorization successful. Tokens saved securely.",
            "request_id": request_id,
        }
        
    except Exception as exc:
        logger.exception(
            "bitrix oauth callback failed",
            extra={"request_id": request_id, "status_code": 500},
        )
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(exc)}")


@app.post("/ingest")
async def telegram_ingest(
    update: TelegramUpdate,
    request: Request,
    _: None = Depends(_enforce_body_size),
):
    """Render worker ingestion endpoint (legacy)."""

    request_id = request.state.request_id
    _enforce_worker_auth(request, config)
    try:
        await process_update(update, config, logger, request_id)
    except Exception:
        logger.exception(
            "telegram update processing failed",
            extra={"request_id": request_id, "status_code": 500},
        )
    return JSONResponse(
        status_code=200, content={"status": "accepted", "request_id": request_id}
    )


def _enforce_worker_auth(request: Request, config: AppConfig) -> None:
    auth_header = request.headers.get("authorization", "")
    if not config.worker_auth_token:
        raise HTTPException(status_code=500, detail="Worker auth token is not set")
    if auth_header != f"Bearer {config.worker_auth_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
