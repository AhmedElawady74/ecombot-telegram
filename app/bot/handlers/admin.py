import csv
import io
from html import escape
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

from app.core.config import ADMIN_IDS
from app.db.base import SessionLocal
from app.db import repo, models
from app.bot.keyboards.admin import (
    admin_menu_kb,
    products_kb,
    product_actions_kb,
    product_edit_menu_kb,
    orders_list_kb,
    order_view_kb,
)
from app.bot.states.admin_product import NewProduct, SetPhoto, EditProduct

router = Router()

def _is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

@router.message(Command("admin"))
async def admin_home(message: types.Message):
    if not _is_admin(message.from_user.id):
        return
    await message.answer("Admin panel:", reply_markup=admin_menu_kb())

# ---------- list products ----------
@router.callback_query(F.data == "adm:products")
async def adm_products(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    async with SessionLocal() as db:
        products = await repo.list_products(db)
    await cb.message.edit_text("Products:", reply_markup=products_kb(products))
    await cb.answer()

@router.callback_query(F.data == "adm:nophoto")
async def adm_products_without_photo(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    async with SessionLocal() as db:
        products = await repo.list_products_without_photo(db)
    text = "Products without photo:" if products else "All products have photos ✅"
    await cb.message.edit_text(text, reply_markup=products_kb(products) if products else admin_menu_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("adm:prod:"))
async def adm_product_view(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    pid = int(cb.data.split(":")[2])
    async with SessionLocal() as db:
        p = await db.get(models.Product, pid)
        cat = await db.get(models.Category, p.category_id) if p else None

    if not p:
        await cb.message.edit_text("Product not found.")
        await cb.answer(); return

    cat_name = cat.name if cat else "—"
    text = f"#{p.id} {p.name}\nPrice: ${float(p.price):.2f}\nCategory: {cat_name}\n\n{p.description or '—'}"
    await cb.message.edit_text(text, reply_markup=product_actions_kb(p.id))
    await cb.answer()

# ---------- edit product ----------
@router.callback_query(F.data.startswith("adm:edit:"))
async def adm_edit_menu(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    pid = int(cb.data.split(":")[2])
    await cb.message.edit_text(f"Edit product #{pid}:", reply_markup=product_edit_menu_kb(pid))
    await cb.answer()

@router.callback_query(F.data.startswith("adm:editfld:"))
async def adm_edit_field_ask(cb: types.CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    _, _, pid, field = cb.data.split(":")
    pid = int(pid)
    await state.clear()
    await state.update_data(product_id=pid, field=field)
    prompt = {
        "name": "Send new name:",
        "price": "Send new price (e.g. 99.90):",
        "category": "Send new category ID (numeric):",
        "description": "Send new description (or '-' to clear):",
    }[field]
    await state.set_state(EditProduct.waiting_value)
    await cb.message.edit_text(prompt)
    await cb.answer()

@router.message(EditProduct.waiting_value)
async def adm_edit_field_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pid = data["product_id"]
    field = data["field"]
    value_raw = message.text.strip()

    async with SessionLocal() as db:
        # validate per-field
        if field == "name":
            if len(value_raw) < 2:
                await message.answer("Name too short."); return
            p = await repo.update_product_fields(db, pid, name=value_raw)

        elif field == "price":
            try:
                price = float(value_raw.replace(",", "."))
            except ValueError:
                await message.answer("Invalid price. Try again."); return
            p = await repo.update_product_fields(db, pid, price=price)

        elif field == "category":
            if not value_raw.isdigit():
                await message.answer("Category ID must be numeric."); return
            cid = int(value_raw)
            cat = await db.get(models.Category, cid)
            if not cat:
                await message.answer("Invalid category ID."); return
            p = await repo.update_product_fields(db, pid, category_id=cid)

        elif field == "description":
            desc = None if value_raw == "-" else value_raw
            p = await repo.update_product_fields(db, pid, description=desc)

        else:
            await message.answer("Unknown field."); return

        cat = await db.get(models.Category, p.category_id)

    await state.clear()
    text = f"Updated:\n#{p.id} {p.name}\nPrice: ${float(p.price):.2f}\nCategory: {cat.name}\n\n{p.description or '—'}"
    await message.answer(text, reply_markup=product_actions_kb(p.id))

# ---------- delete product ----------
@router.callback_query(F.data.startswith("adm:del:"))
async def adm_product_delete(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    pid = int(cb.data.split(":")[2])
    async with SessionLocal() as db:
        await repo.delete_product(db, pid)
        products = await repo.list_products(db)
    await cb.message.edit_text("Deleted. Products:", reply_markup=products_kb(products))
    await cb.answer("Removed")

# ---------- add product (FSM) ----------
@router.callback_query(F.data == "adm:add")
async def adm_add_start(cb: types.CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    await state.clear()
    await cb.message.edit_text("New product → name?")
    await state.set_state(NewProduct.name)
    await cb.answer()

@router.message(NewProduct.name)
async def adm_add_price(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await message.answer("Price? (e.g. 99.90)")
    await state.set_state(NewProduct.price)

@router.message(NewProduct.price)
async def adm_add_category(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Invalid price. Try again (e.g. 99.90)."); return
    await state.update_data(price=price)

    async with SessionLocal() as db:
        cats = await repo.list_categories(db)
    if not cats:
        async with SessionLocal() as db:
            await repo.create_category(db, "General")
            cats = await repo.list_categories(db)

    text = "Category ID?\n" + "\n".join([f"{c.id} – {c.name}" for c in cats])
    await message.answer(text)
    await state.set_state(NewProduct.category)

@router.message(NewProduct.category)
async def adm_add_desc(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Send a numeric category ID from the list above.")
        return
    cid = int(message.text)
    async with SessionLocal() as db:
        cat = await db.get(models.Category, cid)
    if not cat:
        await message.answer("Invalid category ID. Please send an ID from the list shown.")
        return

    await state.update_data(category_id=cid)
    await message.answer("Description? (send '-' to skip)")
    await state.set_state(NewProduct.description)

@router.message(NewProduct.description)
async def adm_add_image(message: types.Message, state: FSMContext):
    desc = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=desc)
    await message.answer("Image URL? (send '-' to skip)")
    await state.set_state(NewProduct.image)

@router.message(NewProduct.image)
async def adm_add_confirm(message: types.Message, state: FSMContext):
    img = None if message.text.strip() == "-" else message.text.strip()
    data = await state.update_data(image_url=img)
    text = (
        "Confirm new product:\n\n"
        f"• Name: {data['name']}\n"
        f"• Price: ${data['price']:.2f}\n"
        f"• Category ID: {data['category_id']}\n"
        f"• Image: {data['image_url'] or '—'}\n"
        f"• Description: {data['description'] or '—'}\n\n"
        "Send 'yes' to save or 'no' to cancel."
    )
    await message.answer(text)
    await state.set_state(NewProduct.confirm)

@router.message(NewProduct.confirm)
async def adm_add_save(message: types.Message, state: FSMContext):
    if message.text.strip().lower() != "yes":
        await state.clear()
        await message.answer("Cancelled."); return
    data = await state.get_data()
    async with SessionLocal() as db:
        p = await repo.create_product(
            db,
            category_id=data["category_id"],
            name=data["name"],
            price=float(data["price"]),
            description=data["description"],
            image_url=data["image_url"]
        )
        products = await repo.list_products(db)
    await state.clear()
    await message.answer(f"Saved: #{p.id} {p.name}\nProducts:", reply_markup=products_kb(products))

# ---------- set photo via file_id ----------
@router.callback_query(F.data.startswith("adm:setphoto:"))
async def adm_ask_photo(cb: types.CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    pid = int(cb.data.split(":")[2])
    await state.clear()
    await state.update_data(product_id=pid)
    await state.set_state(SetPhoto.waiting_photo)
    await cb.message.edit_text(f"Send a photo for product #{pid} (as a PHOTO, not file).")
    await cb.answer()

@router.message(SetPhoto.waiting_photo, F.photo)
async def adm_save_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get("product_id")
    file_id = message.photo[-1].file_id  # highest quality
    async with SessionLocal() as db:
        p = await repo.set_product_photo_file_id(db, pid, file_id)
        products = await repo.list_products(db)
    await state.clear()
    await message.answer(f"Photo saved for #{p.id} {p.name}\nProducts:", reply_markup=products_kb(products))

# ---------- orders ----------
@router.callback_query(F.data.startswith("adm:orders"))
async def adm_orders(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    parts = cb.data.split(":")
    current = parts[2] if len(parts) > 2 else "all"
    async with SessionLocal() as db:
        orders = await repo.list_orders_by_status(db, current, limit=30)
    await cb.message.edit_text(f"Orders (filter: {current})", reply_markup=orders_list_kb(orders, current))
    await cb.answer()

@router.callback_query(F.data.startswith("adm:ord:"))
async def adm_order_view(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    oid = int(cb.data.split(":")[2])
    async with SessionLocal() as db:
        order, items, user = await repo.get_order_with_items(db, oid)
    if not order:
        await cb.message.edit_text("Order not found.", reply_markup=admin_menu_kb())
        await cb.answer(); return

    lines = [
        f"📦 <b>{order.order_number}</b>",
        f"Status: <b>{escape(order.status)}</b>",
        f"Total: <b>${float(order.total):.2f}</b>",
        "",
        "Items:"
    ]
    if items:
        for it in items:
            lines.append(f"• {escape(it['name'])} × {it['qty']} = ${it['qty']*it['price']:.2f}")
    else:
        lines.append("—")

    # user mention
    if user:
        mention = f'<a href="tg://user?id={user.tg_id}">{escape(user.name or str(user.tg_id))}</a>'
        lines.insert(1, f"User: {mention}")

    await cb.message.edit_text("\n".join(lines), reply_markup=order_view_kb(order.id, order.status), parse_mode="HTML")
    await cb.answer()

@router.callback_query(F.data.startswith("adm:ordset:"))
async def adm_order_set_status(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    _, _, oid, status = cb.data.split(":")
    oid = int(oid)
    async with SessionLocal() as db:
        order = await repo.set_order_status(db, oid, status)
        if not order:
            await cb.answer("Order not found", show_alert=True); return
        # load user to notify
        _, _, user = await repo.get_order_with_items(db, oid)

    # notify user
    if user:
        try:
            await cb.bot.send_message(user.tg_id, f"📦 Your order {order.order_number} status is now: {status}")
        except Exception:
            pass

    await cb.answer("Status updated")
    # refresh view
    await adm_order_view(cb)

# ---------- CSV export ----------
@router.callback_query(F.data == "adm:csv30")
async def adm_export_csv(cb: types.CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer(); return
    async with SessionLocal() as db:
        orders = await repo.list_orders_last_days(db, 30)

    # build CSV in memory
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["order_number", "created_at", "status", "user_tg_id", "user_name", "item_name", "qty", "price", "line_total", "order_total"])

    async with SessionLocal() as db:
        for o in orders:
            order, items, user = await repo.get_order_with_items(db, o.id)
            if not items:
                writer.writerow([o.order_number, o.created_at, o.status, user.tg_id if user else "", getattr(user, "name", "") or "", "", "", "", "", float(o.total)])
            else:
                for it in items:
                    writer.writerow([
                        o.order_number, o.created_at, o.status,
                        user.tg_id if user else "", getattr(user, "name", "") or "",
                        it["name"], it["qty"], it["price"], it["qty"] * it["price"], float(o.total)
                    ])

    csv_bytes = buf.getvalue().encode("utf-8-sig")  # BOM for Excel
    file = BufferedInputFile(csv_bytes, filename="orders_last_30_days.csv")
    await cb.message.answer_document(document=file, caption="Orders export (last 30 days)")
    await cb.answer()