import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida ko'rsatilmagan!")
if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS .env faylida ko'rsatilmagan!")
