import os
from dotenv import load_dotenv

# load .env
load_dotenv()

# bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# admin ids as tuple of ints
_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = tuple(int(x.strip()) for x in _raw.split(",") if x.strip().isdigit())