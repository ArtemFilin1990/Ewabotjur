"""FastAPI application setup for Render worker."""

from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.bot.schemas import TelegramUpdate
from src.clients.telegram_client import TelegramClient
from src.config import AppConfig, load_config
from src.files.index import FileProcessor
from src.handlers.telegram_handler import HandlerDependencies, process_update
from src.logging_config import configure_logging, get_logger
from src.security.access_control import AccessController
from src.services.dadata_service import DaDataService
from src.services.risk_service import RiskAnalysisService
from src.services.scoring_service import RiskScoringService
from src.storage.memory_store import JsonMemoryStore


config = load_config()
configure_logging(config.log_level)
logger = get_logger(__name__)

app = FastAPI(title=config.app_name)
telegram_client = TelegramClient(
    token=config.telegram_bot_token,
    base_url=config.telegram_api_base,
    timeout_seconds=config.http_timeout_seconds,
)
dadata_service = DaDataService(
    token=config.dadata_token,
    secret=config.dadata_secret,
    timeout=config.http_timeout_seconds,
)
memory_store = JsonMemoryStore(config.memory_store_path)
dependencies = HandlerDependencies(
    config=config,
    logger=logger,
    telegram=telegram_client,
    dadata=dadata_service,
    scoring=RiskScoringService(),
    risk_analysis=RiskAnalysisService(),
    memory_store=memory_store,
    file_processor=FileProcessor(enable_ocr=config.enable_ocr),
    access_controller=AccessController(
        ",".join([str(item) for item in config.allowed_chat_ids])
    ),
)


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


@app.post("/ingest")
async def ingest_update(
    request: Request,
    _: None = Depends(_enforce_body_size),
):
    """Render worker ingestion endpoint."""

    request_id = request.state.request_id
    auth_header = request.headers.get("authorization")
    expected = f"Bearer {config.worker_auth_token}"
    if auth_header != expected:
        logger.warning(
            "worker auth failed",
            extra={"request_id": request_id, "status_code": 401},
        )
        return JSONResponse(status_code=401, content={"status": "unauthorized"})

    try:
        payload = await request.json()
        update = TelegramUpdate.model_validate(payload)
    except (ValidationError, ValueError) as exc:
        logger.warning(
            "invalid telegram update payload",
            extra={"request_id": request_id, "status_code": 400},
        )
        return JSONResponse(status_code=400, content={"status": "invalid_payload"})

    await process_update(update, dependencies, request_id)
    return JSONResponse(status_code=200, content={"status": "ok"})
