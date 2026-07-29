import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import database
import checker
import worker
import config

logging.basicConfig(level=logging.INFO)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Welcome bhai! Apple pickup track karne ke liye command use kar:\n`/add <URL> <PINCODE>`")

@router.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        await message.reply("❌ Format galat hai. Aise likh:\n`/add <URL> <PINCODE>`")
        return
    args = command.args.split()
    success = database.add_tracking(message.from_user.id, args[0], args[1])
    if success:
        await message.reply(f"✅ Tracking added for Pincode: {args[1]}")
    else:
        await message.reply("⚠️ Yeh item aur pincode tu already track kar raha hai.")

@router.message(Command("remove"))
async def cmd_remove(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        await message.reply("❌ Format galat hai. Aise likh:\n`/remove <URL> <PINCODE>`")
        return
    args = command.args.split()
    success = database.remove_tracking(message.from_user.id, args[0], args[1])
    if success:
        await message.reply(f"✅ Done! Pincode {args[1]} ki tracking delete ho gayi.")
    else:
        await message.reply("❌ Tracking me nahi mili. URL aur Pincode theek se check kar.")

@router.message(Command("list"))
async def cmd_list(message: Message):
    items = database.get_user_tracking(message.from_user.id)
    if not items:
        return await message.reply("Teri tracking list khali hai bhai.")
    msg = "📋 **Teri Tracking List:**\n\n"
    for url, pincode in items:
        msg += f"📍 {pincode} | [Product Link]({url})\n"
    await message.reply(msg, disable_web_page_preview=True)

@router.message(Command("mypickups"))
async def cmd_mypickups(message: Message):
    items = database.get_user_tracking(message.from_user.id)
    if not items:
        return await message.reply("Tu abhi koi item track nahi kar raha.")

    status_msg = await message.reply("⏳ Checking live stock strictly for Apple Store pickup...")
    results_text = "🏬 **Live Pickup Status:**\n\n"
    
    for url, pincode in items:
        result = await checker.check_pickup_strictly(url, pincode)
        if result["status"] == "instock":
            stores_list = ", ".join(result["stores"])
            results_text += f"✅ **IN STOCK**\n📍 {pincode}\n🛒 Stores: {stores_list}\n🔗 [Link]({url})\n\n"
        elif result["status"] == "oos":
            results_text += f"❌ **OUT OF STOCK**\n📍 {pincode}\n🔗 [Link]({url})\n\n"
        else:
            results_text += f"⚠️ **ERROR**\n📍 {pincode}\n🛠 {result.get('message')}\n\n"
            
    await status_msg.edit_text(results_text, disable_web_page_preview=True)

async def main():
    if not config.BOT_TOKEN:
        logging.error("BOT_TOKEN is missing! Set it in environment variables.")
        return

    database.init_db()
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    dp.include_router(router)
    
    # Background worker start kar do
    asyncio.create_task(worker.start_background_worker(bot))
    
    logging.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
