"""Application entrypoint for running the API server."""

from __future__ import annotations

import os

import uvicorn

from src.app import app


def run() -> None:
    """Run the API server with Uvicorn."""

    # ВАЖНО: для Amvera - слушаем порт из переменной окружения PORT
    port = int(os.getenv("PORT", "3000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run()
