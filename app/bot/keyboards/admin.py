from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def admin_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Products", callback_data="adm:products")
    kb.button(text="🖼️ Missing photos", callback_data="adm:nophoto")
    kb.button(text="➕ Add product", callback_data="adm:add")
    kb.button(text="📑 Orders", callback_data="adm:orders:all")
    kb.button(text="📤 Export CSV (30d)", callback_data="adm:csv30")
    kb.adjust(1)
    return kb.as_markup()

def products_kb(products):
    kb = InlineKeyboardBuilder()
    for p in products:
        has_img = bool(getattr(p, "image_file_id", None) or getattr(p, "image_url", None))
        cam = "📷" if has_img else "🚫"
        kb.row(InlineKeyboardButton(text=f"#{p.id} {p.name} {cam}", callback_data=f"adm:prod:{p.id}"))
    kb.row(InlineKeyboardButton(text="⬅️ Back", callback_data="adm:back"))
    return kb.as_markup()

def product_actions_kb(pid: int):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✏️ Edit", callback_data=f"adm:edit:{pid}"),
        InlineKeyboardButton(text="🖼️ Set photo", callback_data=f"adm:setphoto:{pid}"),
    )
    kb.row(InlineKeyboardButton(text="🗑️ Delete", callback_data=f"adm:del:{pid}"))
    kb.row(InlineKeyboardButton(text="⬅️ Back", callback_data="adm:products"))
    return kb.as_markup()

def product_edit_menu_kb(pid: int):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Name", callback_data=f"adm:editfld:{pid}:name"),
        InlineKeyboardButton(text="Price", callback_data=f"adm:editfld:{pid}:price"),
    )
    kb.row(
        InlineKeyboardButton(text="Category", callback_data=f"adm:editfld:{pid}:category"),
        InlineKeyboardButton(text="Description", callback_data=f"adm:editfld:{pid}:description"),
    )
    kb.row(InlineKeyboardButton(text="⬅️ Back", callback_data=f"adm:prod:{pid}"))
    return kb.as_markup()

def orders_list_kb(orders, current_filter: str):
    # first: filters row
    kb = InlineKeyboardBuilder()
    filters = [("all", "All"), ("new", "New"), ("paid", "Paid"), ("shipped", "Shipped"), ("done", "Done")]
    fbtns = [InlineKeyboardButton(
        text=("• " if current_filter == code else "") + label,
        callback_data=f"adm:orders:{code}"
    ) for code, label in filters]
    kb.row(*fbtns)
    kb.row(InlineKeyboardButton(text="📤 Export CSV (30d)", callback_data="adm:csv30"))
    # then: order list
    if orders:
        for o in orders:
            kb.row(InlineKeyboardButton(text=f"{o.order_number} ({o.status})", callback_data=f"adm:ord:{o.id}"))
    kb.row(InlineKeyboardButton(text="⬅️ Back", callback_data="adm:back"))
    return kb.as_markup()

def order_view_kb(order_id: int, current_status: str):
    statuses = ["new", "paid", "shipped", "done"]
    kb = InlineKeyboardBuilder()
    # put status buttons on two rows
    row = []
    for s in statuses:
        prefix = "✅ " if s == current_status else ""
        row.append(InlineKeyboardButton(text=f"{prefix}{s}", callback_data=f"adm:ordset:{order_id}:{s}"))
        if len(row) == 2:
            kb.row(*row); row = []
    if row:
        kb.row(*row)
    kb.row(InlineKeyboardButton(text="⬅️ Back to orders", callback_data="adm:orders:all"))
    return kb.as_markup()