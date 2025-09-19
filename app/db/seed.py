from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models

# simple placeholder images (public demo links)
IMG = {
    "watch_classic":  "https://images.unsplash.com/photo-1511381939415-c1c76de1c0f0",
    "watch_sport":    "https://images.unsplash.com/photo-1524805444758-089113d48a6e",
    "backpack_city":  "https://images.unsplash.com/photo-1514477917009-389c76a86b68",
    "crossbody":      "https://images.unsplash.com/photo-1544441893-675973e31985",
    "sunglasses":     "https://images.unsplash.com/photo-1519681393784-d120267933ba",
    "wallet":         "https://images.unsplash.com/photo-1585386959984-a41552231658",
    "belt":           "https://images.unsplash.com/photo-1592878904946-713f46b6ce5c",
    "bracelet":       "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338",
    "earrings":       "https://images.unsplash.com/photo-1585386958571-5ac7a7f620d9",
    "handbag":        "https://images.unsplash.com/photo-1544441893-80afc9c0fef7",
}

async def seed_if_empty(db: AsyncSession):
    # if there is at least one category, skip seeding
    exists = await db.execute(select(models.Category).limit(1))
    if exists.scalar_one_or_none():
        return

    # ----- categories -----
    cats = {
        "Watches": models.Category(name="Watches"),
        "Bags": models.Category(name="Bags"),
        "Sunglasses": models.Category(name="Sunglasses"),
        "Wallets": models.Category(name="Wallets"),
        "Belts": models.Category(name="Belts"),
        "Jewelry": models.Category(name="Jewelry"),
    }
    db.add_all(list(cats.values()))
    await db.flush()  # ensure IDs are available

    # helper
    def c(name: str) -> int:
        return cats[name].id

    # ----- products -----
    products = [
        # Watches
        models.Product(category_id=c("Watches"), name="Classic Watch",
                       description="Leather strap, 40mm, quartz.",
                       price=99.90, image_url=IMG["watch_classic"]),
        models.Product(category_id=c("Watches"), name="Sport Watch",
                       description="Water resistant 10 ATM, rubber strap.",
                       price=149.00, image_url=IMG["watch_sport"]),
        models.Product(category_id=c("Watches"), name="Minimal Watch",
                       description="Slim case, steel mesh band.",
                       price=129.00),

        # Bags
        models.Product(category_id=c("Bags"), name="City Backpack",
                       description='15" laptop compartment.',
                       price=59.50, image_url=IMG["backpack_city"]),
        models.Product(category_id=c("Bags"), name="Mini Crossbody",
                       description="Vegan leather, magnetic flap.",
                       price=39.00, image_url=IMG["crossbody"]),
        models.Product(category_id=c("Bags"), name="Everyday Handbag",
                       description="Roomy with inner pockets.",
                       price=79.90, image_url=IMG["handbag"]),

        # Sunglasses
        models.Product(category_id=c("Sunglasses"), name="Aviator Shades",
                       description="UV400, polarized lenses.",
                       price=45.00, image_url=IMG["sunglasses"]),
        models.Product(category_id=c("Sunglasses"), name="Round Retro",
                       description="Metal frame, case included.",
                       price=39.00),

        # Wallets
        models.Product(category_id=c("Wallets"), name="Slim Wallet",
                       description="RFID blocking, 6 cards.",
                       price=24.90, image_url=IMG["wallet"]),
        models.Product(category_id=c("Wallets"), name="Zip Wallet",
                       description="Coin pocket, genuine leather.",
                       price=34.90),

        # Belts
        models.Product(category_id=c("Belts"), name="Classic Belt",
                       description="Full-grain leather, 3.5cm.",
                       price=29.00, image_url=IMG["belt"]),
        models.Product(category_id=c("Belts"), name="Reversible Belt",
                       description="Two-tone, brushed buckle.",
                       price=35.00),

        # Jewelry
        models.Product(category_id=c("Jewelry"), name="Leather Bracelet",
                       description="Adjustable, stainless steel clasp.",
                       price=19.90, image_url=IMG["bracelet"]),
        models.Product(category_id=c("Jewelry"), name="Stud Earrings",
                       description="Hypoallergenic, 6mm.",
                       price=14.90, image_url=IMG["earrings"]),
    ]

    db.add_all(products)
    await db.commit()