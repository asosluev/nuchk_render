# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

MENU_FILE = DATA_DIR / "menu.json"
INFO_FILE = DATA_DIR / "info.json"

# Telegram / deployment
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # наприклад: https://your-app.onrender.com
PORT = int(os.getenv("PORT", "8443"))

# меню callback prefix
CB_PREFIX = "menu:"

# адміністратори (можна вказати через ENV ADMIN_IDS="123,456")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip()]

WELCOME_TEXT = "Ласкаво просимо! Оберіть пункт меню."
