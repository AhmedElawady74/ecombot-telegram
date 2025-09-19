from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Confirm", callback_data="co:ok"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="co:cancel"),
    )
    return kb.as_markup()