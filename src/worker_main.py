"""Worker entrypoint for Render deployment."""

from __future__ import annotations

import os

import uvicorn

from src.worker.app import app


def run() -> None:
    """Run the worker API server with Uvicorn."""

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
