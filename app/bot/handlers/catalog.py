from aiogram import Router, F, types
from aiogram.filters import Command
from app.db.base import SessionLocal
from app.db import repo, models
from app.bot.keyboards.catalog import categories_kb, products_kb, product_actions_kb

router = Router()

# nice hero image for the shop "home"
HERO_URL = "https://images.unsplash.com/photo-1520975582071-a28fdf2b1a1a"

# ✅ NEW: make /start show the same view as /shop
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await cmd_shop(message)

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    # list categories with a hero banner
    async with SessionLocal() as db:
        cats = await repo.list_categories(db)
    if not cats:
        await message.answer("No categories yet.")
        return

    try:
        # send a fresh photo with caption + keyboard
        await message.answer_photo(
            photo=HERO_URL,
            caption="Choose a category:",
            reply_markup=categories_kb(cats)
        )
    except Exception:
        # fallback to text if photo fails
        await message.answer("Choose a category:", reply_markup=categories_kb(cats))

@router.callback_query(F.data.startswith("cat:"))
async def on_category(cb: types.CallbackQuery):
    # show products of a category
    category_id = int(cb.data.split(":")[1])
    async with SessionLocal() as db:
        products = await repo.list_products_by_category(db, category_id)
        cat = await db.get(models.Category, category_id)

    if not products:
        # reply as a new message and remove old one to keep chat clean
        await cb.message.answer(
            f"Category: {cat.name}\nNo products yet.",
            reply_markup=categories_kb([cat])
        )
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.answer()
        return

    await cb.message.answer(
        f"Category: {cat.name}\nPick a product:",
        reply_markup=products_kb(products, category_id)
    )
    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.answer()

@router.callback_query(F.data.startswith("prod:"))
async def on_product(cb: types.CallbackQuery):
    # product detail; prefer file_id, then URL; else placeholder; never leave chat blank
    product_id = int(cb.data.split(":")[1])
    async with SessionLocal() as db:
        p = await db.get(models.Product, product_id)

    caption = f"*{p.name}*\n\n{p.description or '—'}\n\nPrice: ${float(p.price):.2f}"
    kb = product_actions_kb(p.id, p.category_id)

    # try file_id
    if p.image_file_id:
        try:
            await cb.message.answer_photo(photo=p.image_file_id, caption=caption, reply_markup=kb, parse_mode="Markdown")
            try: await cb.message.delete()
            except Exception: pass
            await cb.answer()
            return
        except Exception:
            pass

    # try URL (or fallback to HERO_URL)
    url = p.image_url or HERO_URL
    try:
        await cb.message.answer_photo(photo=url, caption=caption, reply_markup=kb, parse_mode="Markdown")
        try: await cb.message.delete()
        except Exception: pass
        await cb.answer()
        return
    except Exception:
        # ultimate fallback: text only
        try:
            await cb.message.edit_text(caption, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            await cb.message.answer(caption, reply_markup=kb, parse_mode="Markdown")
            try: await cb.message.delete()
            except Exception: pass
        await cb.answer()

@router.callback_query(F.data == "back:catlist")
async def back_to_categories(cb: types.CallbackQuery):
    # return to categories and remove photo messages to keep chat clean
    async with SessionLocal() as db:
        cats = await repo.list_categories(db)
    # always send a fresh text/photo message, then delete the old one (photo or text)
    try:
        await cb.message.answer_photo(HERO_URL, caption="Choose a category:", reply_markup=categories_kb(cats))
    except Exception:
        await cb.message.answer("Choose a category:", reply_markup=categories_kb(cats))
    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.answer()

@router.callback_query(F.data.startswith("back:cat:"))
async def back_to_products(cb: types.CallbackQuery):
    # return to product list and remove current message (photo/text)
    category_id = int(cb.data.split(":")[2])
    async with SessionLocal() as db:
        products = await repo.list_products_by_category(db, category_id)
        cat = await db.get(models.Category, category_id)

    await cb.message.answer(
        f"Category: {cat.name}\nPick a product:",
        reply_markup=products_kb(products, category_id)
    )
    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.answer()