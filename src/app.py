"""FastAPI application setup."""

from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.bot.schemas import TelegramUpdate
from src.bot.webhook import handle_update
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


@app.post("/telegram/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    request: Request,
    _: None = Depends(_enforce_body_size),
):
    """Telegram webhook endpoint."""

    request_id = request.state.request_id
    result = handle_update(update, config, logger, request_id)
    return JSONResponse(status_code=result.status_code, content=result.payload)
