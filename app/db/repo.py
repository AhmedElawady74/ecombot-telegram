from datetime import datetime, timedelta
import secrets
from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models

# order number like L-YYMMDD-XXXX
def _gen_order_number() -> str:
    suffix = secrets.token_hex(2).upper()
    return f"L-{datetime.utcnow():%y%m%d}-{suffix}"

# ---------- categories ----------
async def list_categories(db: AsyncSession):
    res = await db.execute(select(models.Category).order_by(models.Category.name))
    return res.scalars().all()

async def create_category(db: AsyncSession, name: str):
    c = models.Category(name=name)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c

# ---------- products ----------
async def list_products(db: AsyncSession, limit: int = 50):
    res = await db.execute(select(models.Product).order_by(models.Product.id.desc()).limit(limit))
    return res.scalars().all()

async def list_products_by_category(db: AsyncSession, category_id: int):
    res = await db.execute(
        select(models.Product)
        .where(models.Product.category_id == category_id, models.Product.is_active == True)
        .order_by(models.Product.name)
    )
    return res.scalars().all()

async def list_products_without_photo(db: AsyncSession):
    res = await db.execute(
        select(models.Product).where(
            models.Product.image_file_id.is_(None),
            models.Product.image_url.is_(None)
        ).order_by(models.Product.id.desc())
    )
    return res.scalars().all()

async def create_product(
    db: AsyncSession,
    category_id: int,
    name: str,
    price: float,
    description: str | None = None,
    image_url: str | None = None,
    is_active: bool = True,
):
    p = models.Product(
        category_id=category_id,
        name=name,
        price=price,
        description=description,
        image_url=image_url,
        is_active=is_active,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p

async def update_product_fields(db: AsyncSession, product_id: int, **fields):
    p = await db.get(models.Product, product_id)
    if not p:
        return None
    for k, v in fields.items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return p

async def delete_product(db: AsyncSession, product_id: int):
    await db.execute(delete(models.Product).where(models.Product.id == product_id))
    await db.commit()

async def set_product_photo_file_id(db: AsyncSession, product_id: int, file_id: str):
    p = await db.get(models.Product, product_id)
    if not p:
        return None
    p.image_file_id = file_id
    await db.commit()
    return p

# ---------- users ----------
async def get_or_create_user(db: AsyncSession, tg_id: int):
    res = await db.execute(select(models.User).where(models.User.tg_id == tg_id))
    user = res.scalar_one_or_none()
    if not user:
        user = models.User(tg_id=tg_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

async def update_user_details(db: AsyncSession, tg_id: int, name: str, phone: str, address: str):
    user = await get_or_create_user(db, tg_id)
    user.name, user.phone, user.address = name, phone, address
    await db.commit()
    return user

# ---------- cart ----------
async def add_to_cart(db: AsyncSession, user_id: int, product_id: int, qty: int = 1):
    res = await db.execute(
        select(models.CartItem).where(
            models.CartItem.user_id == user_id, models.CartItem.product_id == product_id
        )
    )
    item = res.scalar_one_or_none()
    if item:
        item.qty += qty
    else:
        item = models.CartItem(user_id=user_id, product_id=product_id, qty=qty)
        db.add(item)
    await db.commit()
    return item

async def get_cart(db: AsyncSession, user_id: int):
    res = await db.execute(select(models.CartItem).where(models.CartItem.user_id == user_id))
    items = res.scalars().all()
    total = 0.0
    for it in items:
        p = await db.get(models.Product, it.product_id)
        total += float(p.price) * it.qty
    return items, round(total, 2)

async def change_qty(db: AsyncSession, item_id: int, delta: int):
    item = await db.get(models.CartItem, item_id)
    if not item:
        return None
    item.qty = max(1, item.qty + delta)
    await db.commit()
    return item

async def remove_item(db: AsyncSession, item_id: int):
    await db.execute(delete(models.CartItem).where(models.CartItem.id == item_id))
    await db.commit()

async def clear_cart(db: AsyncSession, user_id: int):
    await db.execute(delete(models.CartItem).where(models.CartItem.user_id == user_id))
    await db.commit()

# ---------- orders ----------
async def create_order(db: AsyncSession, user_id: int):
    items, total = await get_cart(db, user_id)
    if not items:
        return None
    order = models.Order(user_id=user_id, total=total, status="new", order_number=_gen_order_number())
    db.add(order)
    await db.commit()
    await db.refresh(order)
    for it in items:
        p = await db.get(models.Product, it.product_id)
        db.add(models.OrderItem(order_id=order.id, product_id=p.id, qty=it.qty, price=p.price))
    await db.commit()
    await clear_cart(db, user_id)
    return order

async def list_orders(db: AsyncSession, limit: int = 20):
    res = await db.execute(select(models.Order).order_by(desc(models.Order.created_at)).limit(limit))
    return res.scalars().all()

async def list_orders_by_status(db: AsyncSession, status: str | None, limit: int = 30):
    stmt = select(models.Order).order_by(desc(models.Order.created_at)).limit(limit)
    if status and status != "all":
        stmt = stmt.where(models.Order.status == status)
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_order_with_items(db: AsyncSession, order_id: int):
    order = await db.get(models.Order, order_id)
    if not order:
        return None, [], None
    # items + product names
    res = await db.execute(
        select(models.OrderItem, models.Product.name)
        .join(models.Product, models.Product.id == models.OrderItem.product_id)
        .where(models.OrderItem.order_id == order_id)
    )
    rows = res.all()
    items = [{"name": name, "qty": oi.qty, "price": float(oi.price)} for (oi, name) in rows]
    user = await db.get(models.User, order.user_id)
    return order, items, user

async def set_order_status(db: AsyncSession, order_id: int, status: str):
    order = await db.get(models.Order, order_id)
    if not order:
        return None
    order.status = status
    await db.commit()
    await db.refresh(order)
    return order

async def list_orders_last_days(db: AsyncSession, days: int = 30):
    since = datetime.utcnow() - timedelta(days=days)
    res = await db.execute(
        select(models.Order).where(models.Order.created_at >= since).order_by(desc(models.Order.created_at))
    )
    return res.scalars().all()