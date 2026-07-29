import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
import database
from bot import router

# Logging setup taaki Railway console me sab dikhe
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

async def setup_bot_commands(bot: Bot):
    """Telegram app me Menu button set karne ke liye"""
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="add", description="Add URL and Pincode"),
        BotCommand(command="remove", description="Remove a tracked item"),
        BotCommand(command="list", description="View tracked items"),
        BotCommand(command="mypickups", description="Check stock status right now")
    ]
    await bot.set_my_commands(commands)
    logging.info("Bot commands menu registered.")

async def main():
    # 1. Database initialize karo
    database.init_db()

    # 2. Bot setup karo
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # 3. Menu commands set karo
    await setup_bot_commands(bot)

    # Note: Jab tera worker.py poori tarah ready ho jayega, 
    # tab yahan hum asyncio.create_task(worker_loop) add karenge.

    # 4. Polling start karo
    try:
        logging.info("Bot is starting...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
