import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from bot import router
from worker import start_background_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

async def main():
    # 1. Init Database
    init_db()

    # 2. Setup Bot
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # 3. Start Background Worker Loop
    worker_task = asyncio.create_task(start_background_worker(bot))

    # 4. Start Polling
    try:
        logging.info("Bot is starting...")
        await dp.start_polling(bot)
    finally:
        worker_task.cancel()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
