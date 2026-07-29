import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database import add_tracking, get_all_combos

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Hello! Send /add <URL> <PINCODE> to track Apple Pickup.")

@router.message(Command("add"))
async def cmd_add(message: Message):
    # Command expected: /add https://apple.com/... 110001
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Usage: /add <Apple URL> <Pincode>")
        return
    
    url = args[1]
    pincode = args[2]
    user_id = message.from_user.id

    success = add_tracking(user_id, url, pincode)
    if success:
        await message.answer(f"✅ Tracking added for Pincode: {pincode}")
    else:
        await message.answer("⚠️ This URL + Pincode combo is already being tracked.")

@router.message(Command("list"))
async def cmd_list(message: Message):
    combos = get_all_combos()
    user_combos = [c for c in combos if c["user_id"] == message.from_user.id]
    
    if not user_combos:
        await message.answer("You are not tracking anything.")
        return
        
    text = "📋 **Your Tracked Items:**\n"
    for i, c in enumerate(user_combos, 1):
        text += f"{i}. Pincode: {c['pincode']} | URL: {c['url']}\n"
    
    await message.answer(text)
