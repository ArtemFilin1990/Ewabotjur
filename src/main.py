"""Application entrypoint for running the API server."""

from __future__ import annotations

import os

import uvicorn

from src.app import app


def run() -> None:
    """Run the API server with Uvicorn."""

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
