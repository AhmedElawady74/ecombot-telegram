from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ Go to shop", callback_data="back:catlist")
    await message.answer("Hi 👋\nI'm your e-commerce bot!", reply_markup=kb.as_markup())