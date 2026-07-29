from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
import database
import checker

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "Welcome bhai! Apple pickup track karne ke liye command use kar:\n"
        "`/add <URL> <PINCODE>`"
    )

@router.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("❌ Format galat hai. Aise likh:\n`/add <URL> <PINCODE>`")
        return
    
    args = command.args.split()
    if len(args) < 2:
        await message.reply("❌ URL aur Pincode dono dena zaroori hai.")
        return
        
    url, pincode = args[0], args[1]
    success = database.add_tracking(message.from_user.id, url, pincode)
    
    if success:
        await message.reply(f"✅ Tracking added for Pincode: {pincode}")
    else:
        await message.reply("⚠️ Yeh item aur pincode tu already track kar raha hai.")

@router.message(Command("remove"))
async def cmd_remove(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("❌ Format galat hai. Aise likh:\n`/remove <URL> <PINCODE>`")
        return
        
    args = command.args.split()
    if len(args) < 2:
        await message.reply("❌ URL aur Pincode dono dena zaroori hai.")
        return
        
    url, pincode = args[0], args[1]
    success = database.remove_tracking(message.from_user.id, url, pincode)
    
    if success:
        await message.reply(f"✅ Done! Pincode {pincode} ki tracking delete ho gayi hai.")
    else:
        await message.reply("❌ Yeh tracking list me nahi mili. URL aur Pincode theek se check kar.")

@router.message(Command("list"))
async def cmd_list(message: Message):
    items = database.get_user_tracking(message.from_user.id)
    if not items:
        await message.reply("Teri tracking list khali hai bhai.")
        return
        
    msg = "📋 **Teri Tracking List:**\n\n"
    for url, pincode in items:
        msg += f"📍 Pincode: {pincode}\n🔗 URL: {url}\n\n"
    
    await message.reply(msg, disable_web_page_preview=True)

@router.message(Command("mypickups"))
async def cmd_mypickups(message: Message):
    items = database.get_user_tracking(message.from_user.id)
    if not items:
        await message.reply("Bhai, tu abhi koi item track nahi kar raha. Pehle `/add <URL> <PINCODE>` use kar.")
        return

    # User ko waiting message bhejna
    status_msg = await message.reply("⏳ Checking live stock strictly for Apple Store pickup... thoda wait kar bhai.")

    results_text = "🏬 **Live Pickup Status:**\n\n"
    
    for url, pincode in items:
        # Naye strict checker ko call karna
        result = await checker.check_pickup_strictly(url, pincode)
        
        if result["status"] == "instock":
            stores_list = ", ".join(result["stores"])
            results_text += f"✅ **IN STOCK (Pickup Available)**\n📍 Pincode: {pincode}\n🛒 Stores: {stores_list}\n🔗 [Product Link]({url})\n\n"
        
        elif result["status"] == "oos":
            results_text += f"❌ **OUT OF STOCK (No Pickup)**\n📍 Pincode: {pincode}\n🔗 [Product Link]({url})\n\n"
        
        else:
            error_msg = result.get("message", "Unknown error")
            results_text += f"⚠️ **ERROR**\n📍 Pincode: {pincode}\n🛠 Issue: {error_msg}\n🔗 [Product Link]({url})\n\n"

    # Waiting message ko final result se replace karna
    await status_msg.edit_text(results_text, disable_web_page_preview=True)
