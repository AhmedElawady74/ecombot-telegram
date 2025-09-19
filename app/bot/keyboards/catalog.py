from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.db import models

# small emoji map for nicer look
EMOJI = {
    "Bags": "👜",
    "Belts": "🧣",         # belt emoji doesn't exist; scarf works visually
    "Jewelry": "💍",
    "Sunglasses": "🕶️",
    "Wallets": "👝",
    "Watches": "⌚",
}

def categories_kb(categories: list[models.Category]):
    """Inline keyboard for categories (3 per row) with emojis."""
    kb = InlineKeyboardBuilder()
    for c in categories:
        title = f"{EMOJI.get(c.name, '•')} {c.name}"
        kb.button(text=title, callback_data=f"cat:{c.id}")
    kb.adjust(3)  # 3 buttons per row
    return kb.as_markup()

def products_kb(products: list[models.Product], category_id: int):
    """Products of a category + back buttons."""
    kb = InlineKeyboardBuilder()
    for p in products:
        kb.button(text=p.name, callback_data=f"prod:{p.id}")
    # navigation
    kb.button(text="⬅️ Back to categories", callback_data="back:catlist")
    kb.adjust(2)  # 2 per row for readability
    return kb.as_markup()

def product_actions_kb(product_id: int, category_id: int):
    """Actions under a product card."""
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add to cart", callback_data=f"add:{product_id}")
    kb.button(text="✅ Checkout", callback_data="checkout")
    kb.button(text="🛍 Continue shopping", callback_data=f"back:cat:{category_id}")
    kb.adjust(1)
    return kb.as_markup()