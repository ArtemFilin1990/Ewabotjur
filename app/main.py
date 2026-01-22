import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.config import BOT_TOKEN, LOG_LEVEL
from app.bot.router import router

async def main():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
