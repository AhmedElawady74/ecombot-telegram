from aiogram import Router, F, types
from aiogram.filters import Command
from app.db.base import SessionLocal
from app.db import repo
from app.bot.keyboards.cart import cart_kb  # reuse one import

router = Router()

@router.callback_query(F.data.startswith("add:"))
async def on_add_to_cart(cb: types.CallbackQuery):
    # add product to cart
    product_id = int(cb.data.split(":")[1])
    async with SessionLocal() as db:
        user = await repo.get_or_create_user(db, cb.from_user.id)
        await repo.add_to_cart(db, user.id, product_id, qty=1)
    await cb.answer("Added to cart ✅", show_alert=False)

@router.message(Command("cart"))
async def cmd_cart(message: types.Message):
    # show cart with totals
    async with SessionLocal() as db:
        user = await repo.get_or_create_user(db, message.from_user.id)
        items, total = await repo.get_cart(db, user.id)

        if not items:
            await message.answer("Your cart is empty.")
            return

        # build lines with product names
        from app.db import models
        lines = [f"🛒 Your cart (total: ${total:.2f}):"]
        for it in items:
            p = await db.get(models.Product, it.product_id)
            lines.append(f"• {p.name} × {it.qty}")

    await message.answer("\n".join(lines), reply_markup=cart_kb(items))

@router.callback_query(F.data.startswith("qty:"))
async def change_qty(cb: types.CallbackQuery):
    # increment/decrement quantity
    sign, item_id = cb.data.split(":")[1], int(cb.data.split(":")[2])
    delta = 1 if sign == "+" else -1

    async with SessionLocal() as db:
        await repo.change_qty(db, item_id, delta)
        user = await repo.get_or_create_user(db, cb.from_user.id)
        items, total = await repo.get_cart(db, user.id)

        from app.db import models
        lines = [f"🛒 Your cart (total: ${total:.2f}):"]
        for it in items:
            p = await db.get(models.Product, it.product_id)
            lines.append(f"• {p.name} × {it.qty}")

    await cb.message.edit_text("\n".join(lines), reply_markup=cart_kb(items))
    await cb.answer()

@router.callback_query(F.data.startswith("rm:"))
async def remove_item(cb: types.CallbackQuery):
    # remove one item from cart
    item_id = int(cb.data.split(":")[1])

    async with SessionLocal() as db:
        await repo.remove_item(db, item_id)
        user = await repo.get_or_create_user(db, cb.from_user.id)
        items, total = await repo.get_cart(db, user.id)

        from app.db import models
        if not items:
            await cb.message.edit_text("Your cart is empty.")
            await cb.answer()
            return

        lines = [f"🛒 Your cart (total: ${total:.2f}):"]
        for it in items:
            p = await db.get(models.Product, it.product_id)
            lines.append(f"• {p.name} × {it.qty}")

    await cb.message.edit_text("\n".join(lines), reply_markup=cart_kb(items))
    await cb.answer()