"""FastAPI app for Render worker ingestion."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.handlers.telegram_worker import process_update
from src.logging_config import configure_logging, get_logger
from src.storage.memory_store import MemoryStore
from src.worker.config import load_worker_config


config = load_worker_config()
configure_logging(config.log_level)
logger = get_logger(__name__)
memory_store = MemoryStore(config.memory_store_path)

app = FastAPI(title=config.app_name)


def _get_request_id(request: Request) -> str:
    header_name = config.request_id_header
    return request.headers.get(header_name, str(uuid4()))


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = _get_request_id(request)
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[config.request_id_header] = request_id
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""

    return {
        "status": "ok",
        "app": config.app_name,
        "environment": config.environment,
    }


@app.post("/ingest")
async def ingest_update(request: Request):
    """Process updates forwarded from Vercel webhook."""

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header.replace("Bearer ", "", 1).strip()
    if not token or token != config.worker_auth_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not config.telegram_bot_token:
        raise HTTPException(status_code=500, detail="Telegram token is missing")

    try:
        update = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    request_id = request.state.request_id
    try:
        process_update(update, config, memory_store)
    except Exception:
        logger.exception(
            "worker processing failed",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=500,
            content={"status": "error", "request_id": request_id},
        )
    return JSONResponse(status_code=200, content={"status": "ok", "request_id": request_id})
