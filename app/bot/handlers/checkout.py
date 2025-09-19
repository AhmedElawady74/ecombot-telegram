import re
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bot.states.checkout import CheckoutStates
from app.db.base import SessionLocal
from app.db import repo
from app.core.config import ADMIN_IDS

router = Router()

_phone_re = re.compile(r"^[+0-9][0-9\s\-()]{5,}$")

@router.callback_query(F.data == "checkout")
async def start_checkout(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("Your name?")
    await state.set_state(CheckoutStates.name)
    await cb.answer()

@router.message(CheckoutStates.name)
async def ask_phone(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Please enter a valid name.")
        return
    await state.update_data(name=name)
    await message.answer("Phone number? (e.g. +123456789)")
    await state.set_state(CheckoutStates.phone)

@router.message(CheckoutStates.phone)
async def ask_shipping(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not _phone_re.match(phone):
        await message.answer("Please enter a valid phone number (digits, +, -, space).")
        return
    await state.update_data(phone=phone)

    kb = InlineKeyboardBuilder()
    kb.button(text="🚚 Courier", callback_data="ship:courier")
    kb.button(text="🏬 Pickup", callback_data="ship:pickup")
    kb.adjust(2)
    await message.answer("Choose shipping method:", reply_markup=kb.as_markup())
    await state.set_state(CheckoutStates.shipping)

@router.callback_query(CheckoutStates.shipping, F.data.startswith("ship:"))
async def ask_address(cb: types.CallbackQuery, state: FSMContext):
    method = cb.data.split(":")[1]
    await state.update_data(shipping=method)
    await cb.message.edit_text("Delivery address?")
    await state.set_state(CheckoutStates.address)
    await cb.answer()

@router.message(CheckoutStates.address)
async def confirm(message: types.Message, state: FSMContext):
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("Address looks too short. Try again.")
        return
    data = await state.update_data(address=address)
    text = (
        "Please confirm your order details:\n\n"
        f"• Name: {data['name']}\n"
        f"• Phone: {data['phone']}\n"
        f"• Shipping: {data.get('shipping','—')}\n"
        f"• Address: {data['address']}\n\n"
        "Confirm?"
    )
    from app.bot.keyboards.checkout import confirm_kb
    await message.answer(text, reply_markup=confirm_kb())
    await state.set_state(CheckoutStates.confirm)

@router.callback_query(CheckoutStates.confirm, F.data.in_(("co:ok", "co:cancel")))
async def finalize(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if cb.data == "co:cancel":
        await state.clear()
        await cb.message.edit_text("Checkout cancelled.")
        await cb.answer()
        return

    # persist user details + create order
    async with SessionLocal() as db:
        user = await repo.update_user_details(db, cb.from_user.id, data["name"], data["phone"], data["address"])
        order = await repo.create_order(db, user.id)

    await state.clear()
    await cb.message.edit_text(
        f"✅ Order placed!\nOrder № {order.order_number}\nTotal: ${float(order.total):.2f}"
    )

    # notify admins
    ship = data.get("shipping", "—")
    if ADMIN_IDS:
        for admin_id in ADMIN_IDS:
            try:
                await cb.bot.send_message(
                    admin_id,
                    f"🆕 New order {order.order_number}\n"
                    f"User: @{cb.from_user.username or cb.from_user.id}\n"
                    f"Shipping: {ship}\n"
                    f"Total: ${float(order.total):.2f}\nStatus: {order.status}"
                )
            except Exception:
                pass

    await cb.answer()