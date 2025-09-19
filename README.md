# 🛒 E-commerce Telegram Bot

A fully functional **Telegram E-commerce Bot** built with [Aiogram 3.x](https://docs.aiogram.dev/) and Python.
The bot allows customers to browse categories, view products with images, manage their cart, checkout with shipping options, and place orders.
It also provides an **admin panel** to manage products and orders directly inside Telegram.

---

## 🚀 Features

### 👤 User Features

* `/start` – Welcome message and entry point.
* `/shop` – Browse product categories.
* Inline keyboards for:

  * Viewing products (with images, description, and price).
  * Adding/removing items to cart.
  * Updating item quantities.
* `/cart` – View cart, change quantities, remove items.
* Checkout process with:

  * Name
  * Phone (validated)
  * Shipping method (Courier / Pickup)
  * Delivery address
* Order confirmation and summary.
* Clean and user-friendly interface with inline buttons.

### 🔑 Admin Features

* `/admin` – Access to admin panel (restricted by **Telegram user IDs**).
* Product Management:

  * List all products.
  * Add new product (with name, price, category, description, and image).
  * Edit existing product.
  * Delete product.
  * Set product photo directly from Telegram.
* Order Management:

  * View recent orders.
  * Filter by status (`new`, `paid`, `shipped`, `done`).
  * Update order status with automatic user notification.
* Export orders as CSV for the last 30 days.

---

## 🛠️ Tech Stack

* **Python 3.10+**
* **Aiogram 3.x** (Telegram Bot framework)
* **SQLite** (default DB – simple and lightweight)
* **SQLAlchemy** (async ORM)
* **FSM (Finite State Machine)** for checkout and admin product creation
* **Docker-ready** (easy deployment)

---

## 📂 Project Structure

```
app/
├── bot/
│   ├── handlers/        # User and Admin handlers
│   ├── keyboards/       # Inline keyboard builders
│   ├── states/          # FSM states
│   └── main.py          # Bot entry point
├── core/
│   └── config.py        # Configurations (BOT_TOKEN, ADMIN_IDS, DB settings)
├── db/
│   ├── base.py          # Async session maker
│   ├── models.py        # SQLAlchemy models
│   └── repo.py          # DB operations
└── ecom.db              # SQLite database (auto-created)
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo

```bash
git clone https://github.com/AhmedElawady74/ecombot-telegram
cd ecombot
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Edit `app/core/config.py`:

```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_IDS = [123456789]  # your Telegram user ID(s)
```

To get your Telegram ID: open [@userinfobot](https://t.me/userinfobot).

### 5. Run migrations (first time only)

```bash
python -m app.db.base
```

### 6. Run the bot

```bash
python -m app.bot.main
```

---

## 🖼️ Screenshots

### User Flow

* Browse categories & products
* View product details with images
* Add to cart → Checkout → Place order

### Admin Flow

* Manage products (add/edit/delete/set photo)
* Manage orders with status updates

---

## 📦 Deployment

You can run this bot on:

* Local machine
* VPS
* Docker (Dockerfile included)

Example (Docker):

```bash
docker build -t ecombot .
docker run -d --name ecombot ecombot
```

---

## 🔐 Security Notes

* Admin access is restricted by **Telegram User IDs**.
* Always keep your `BOT_TOKEN` secret.
* Use environment variables or a `.env` file in production.

---

## 📊 Future Improvements

* Payment integration (Stripe/PayPal/Telegram Payments API).
* Multi-language support.
* Analytics dashboard.
* Product stock management.

---

## 👨‍💻 Author

Developed as a **Telegram E-commerce Bot demo project**.
Feel free to fork, use, and improve!
Made by @AElawadi74
