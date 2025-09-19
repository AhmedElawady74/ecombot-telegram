from aiogram.utils.keyboard import InlineKeyboardBuilder

def cart_kb(items):
    kb = InlineKeyboardBuilder()
    for it in items:
        kb.button(text=f"➖", callback_data=f"qty:-:{it.id}")
        kb.button(text=f"{it.qty}", callback_data="noop")
        kb.button(text=f"➕", callback_data=f"qty:+:{it.id}")
        kb.button(text=f"🗑️ Remove", callback_data=f"rm:{it.id}")
        kb.adjust(4)
    kb.button(text="✅ Checkout", callback_data="checkout")
    kb.button(text="🛍️ Continue shopping", callback_data="back:catlist")
    kb.adjust(1)
    return kb.as_markup()