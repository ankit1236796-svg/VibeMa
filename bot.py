import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from checkers.apple import AppleChecker
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Tracked products: {sku: [pincodes]}
TRACKED_PRODUCTS = {
    "MG6K4HN/A": ["110017", "400051", "201301"],  # iPhone 17 White
    "MG6L4HN/A": ["110017", "400051"],            # iPhone 17 Mist Blue
}

async def check_all_pickup():
    """Check all tracked products and send alerts."""
    async with AppleChecker() as checker:
        tasks = []
        for sku, pincodes in TRACKED_PRODUCTS.items():
            for pincode in pincodes:
                tasks.append(checker.check_pickup(sku, pincode))

        results = await asyncio.gather(*tasks)

        for result in results:
            if not result.success:
                logger.warning(f"Check failed for {result.sku}/{result.pincode}: {result.error}")
                continue

            for store in result.availability:
                if store.available:
                    await send_alert(store)
                    break  # Alert once per SKU/pincode

async def send_alert(store: StoreAvailability):
    """Send Telegram alert for available pickup."""
    message = (
        f"🚨 *STOCK ALERT!* 🚨\n\n"
        f"📱 *Product:* iPhone 17 ({store.sku})\n"
        f"📍 *Store:* {store.store_name} ({store.pincode})\n"
        f"✅ *Status:* **IN STOCK** for pickup!\n"
        f"🕒 *Time:* {store.last_checked.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await bot.send_message(config.CHAT_ID, message, parse_mode="Markdown")

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("🤖 Apple Pickup Alert Bot is running! Use /check to manually check stock.")

@dp.message(Command("check"))
async def check_command(message: types.Message):
    await message.answer("⏳ Checking stock...")
    await check_all_pickup()
    await message.answer("✅ Stock check completed!")

@dp.message()
async def echo(message: types.Message):
    await message.answer("Use /start or /check")

async def scheduler():
    """Run checks every 3 minutes."""
    while True:
        await check_all_pickup()
        await asyncio.sleep(180)  # 3 minutes

async def main():
    # Start scheduler
    asyncio.create_task(scheduler())
    # Start bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
