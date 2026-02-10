"""FastAPI entrypoint for Ewabotjur."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status

from src.config import settings
from src.db.migrate import migrate
from src.integrations.bitrix24.oauth import handle_oauth_callback, initiate_oauth
from src.transport.telegram.handlers import handle_update
from src.utils.http import close_http_client
from src.utils.logging import configure_logging, reset_request_id, set_request_id

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def _split_bracket_key(key: str) -> list[str]:
    """Split bitrix form keys like data[USER][ID] into parts."""
    parts: list[str] = []
    current = ""
    for char in key:
        if char in "[]":
            if current:
                parts.append(current)
                current = ""
            continue
        current += char
    if current:
        parts.append(current)
    return parts


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application startup", extra={"operation": "startup", "result": "success"})
    if settings.database_url:
        try:
            await migrate()
        except Exception:
            logger.error(
                "Database migration failed during startup",
                extra={
                    "operation": "startup.db_migrate",
                    "result": "error",
                    "startup_db_required": settings.startup_db_required,
                },
                exc_info=True,
            )
            if settings.startup_db_required:
                raise
            logger.warning(
                "Continuing startup in degraded mode because STARTUP_DB_REQUIRED is false",
                extra={"operation": "startup.db_migrate", "result": "warning"},
            )
    else:
        logger.warning("DATABASE_URL is empty", extra={"operation": "startup", "result": "warning"})
    yield
    await close_http_client()
    logger.info("Application shutdown", extra={"operation": "shutdown", "result": "success"})


app = FastAPI(title="Ewabotjur", version="2.0.0", lifespan=lifespan)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    token = set_request_id(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "Request processed",
            extra={"operation": "http_request", "result": "success", "duration_ms": duration_ms, "request_id": request_id},
        )
        reset_request_id(token)


@app.get("/")
async def root():
    return {"service": "Ewabotjur", "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/webhook/telegram/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != settings.tg_webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook secret")

    update_data = await request.json()
    try:
        await handle_update(update_data)
    except Exception:
        logger.error(
            "Telegram webhook processing failed",
            extra={"operation": "telegram.webhook", "result": "error", "update_id": update_data.get("update_id")},
            exc_info=True,
        )
    return {"ok": True}


@app.get("/oauth/bitrix/callback")
async def oauth_bitrix_callback(code: str | None = None, domain: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")
    _ = domain
    return await handle_oauth_callback(code)


@app.get("/oauth/bitrix/start")
async def oauth_bitrix_start(domain: str | None = None):
    _ = domain
    return {"auth_url": initiate_oauth()}
