import asyncio
import logging
from database import get_all_combos
from checker import fetch_pickup_availability
from config import STAGGER_INTERVAL_SECONDS

logger = logging.getLogger(__name__)

async def process_single_combo(bot, user_id, url, pincode):
    """Background task to check availability without blocking the main loop."""
    try:
        is_available = await fetch_pickup_availability(url, pincode)
        if is_available:
            # Telegram alert bhejne ka logic
            await bot.send_message(user_id, f"✅ Pickup Available!\n📍 Pincode: {pincode}\n🔗 {url}")
            logger.info(f"Alert sent to {user_id} for {pincode}")
    except Exception as e:
        logger.error(f"Error processing combo {pincode}: {e}")

async def start_background_worker(bot):
    logger.info("Background worker started...")
    while True:
        combos = get_all_combos()
        
        if not combos:
            await asyncio.sleep(10)
            continue

        for combo in combos:
            # 🔥 Fire and Forget: Creates a background task, DOES NOT block the loop
            asyncio.create_task(
                process_single_combo(bot, combo["user_id"], combo["url"], combo["pincode"])
            )
            
            # Sirf stagger interval ka chhota delay
            await asyncio.sleep(STAGGER_INTERVAL_SECONDS)
