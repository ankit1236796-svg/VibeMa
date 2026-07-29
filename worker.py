import asyncio
import logging
from aiogram import Bot
import database
import checker
import config

logger = logging.getLogger(__name__)

# Memory me last status yaad rakhne ke liye taaki spam na ho
# format: {(user_id, url, pincode): "instock" | "oos"}
_last_status = {}

async def check_and_alert(bot: Bot, user_id, url, pincode):
    try:
        result = await checker.check_pickup_strictly(url, pincode)
        current_status = result["status"]
        cache_key = (user_id, url, pincode)
        
        last_state = _last_status.get(cache_key, "oos")

        if current_status == "instock" and last_state != "instock":
            stores = ", ".join(result.get("stores", []))
            msg = f"🚨 **RESTOCK ALERT! (Apple Pickup)**\n📍 Pincode: {pincode}\n🛒 Stores: {stores}\n🔗 [Buy Here]({url})"
            await bot.send_message(user_id, msg, disable_web_page_preview=True)
            _last_status[cache_key] = "instock"
            
        elif current_status == "oos" and last_state == "instock":
            _last_status[cache_key] = "oos"

    except Exception as e:
        logger.error(f"Worker Error for {pincode}: {e}")

async def start_background_worker(bot: Bot):
    logger.info("Background Worker Started...")
    while True:
        tracking_list = database.get_all_tracking()
        
        if not tracking_list:
            await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)
            continue
            
        for user_id, url, pincode in tracking_list:
            # Fire and forget: Main loop ko block nahi karega
            asyncio.create_task(check_and_alert(bot, user_id, url, pincode))
            await asyncio.sleep(config.STAGGER_INTERVAL_SECONDS)
            
        # Pura loop khatam hone ke baad interval wait karega
        await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)
