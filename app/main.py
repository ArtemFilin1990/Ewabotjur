"""Telegram bot entrypoint (polling)."""

from __future__ import annotations

import asyncio
import contextlib
import signal

from aiogram import Bot, Dispatcher

from app.bot.handlers import setup_handlers
from app.config import load_config
from app.storage.memory import MemoryStore
from app.utils.logging import configure_logging, get_logger


logger = get_logger(__name__)


def _setup_signals(stop_event: asyncio.Event) -> None:
    def _handler(*_: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


async def run_bot() -> None:
    """Run the bot in polling mode."""

    config = load_config()
    configure_logging(config.log_level)

    bot = Bot(token=config.bot_token)
    dispatcher = Dispatcher()

    memory = MemoryStore(config.memory_db_path)
    await memory.initialize()

    setup_handlers(dispatcher.router, config, memory)

    stop_event = asyncio.Event()
    _setup_signals(stop_event)

    logger.info("bot starting", extra={"status": "starting", "module": "bot"})

    polling_task = asyncio.create_task(dispatcher.start_polling(bot))
    await stop_event.wait()
    polling_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await polling_task


async def main() -> None:
    """Main async entrypoint."""

    try:
        await run_bot()
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "bot crashed",
            extra={"status": "error", "module": "bot", "error_type": type(exc).__name__},
        )
        raise


if __name__ == "__main__":
    asyncio.run(main())
