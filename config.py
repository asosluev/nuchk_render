# config.py
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()  # прочитати .env, якщо є

BASE_DIR = Path(__file__).parent
TOKEN = os.getenv('TG_BOT_TOKEN', 'PUT_YOUR_TOKEN_HERE')

# ADMINS: перелік рядків, може бути id (як рядок) або @username
ADMINS = [x.strip() for x in os.getenv('TG_ADMINS', '').split(',') if x.strip()]

DATA_DIR = BASE_DIR / 'data'
MENU_FILE = DATA_DIR / 'menu.json'
INFO_FILE = DATA_DIR / 'info.json'

# Callback prefix — для розпізнавання наших callback-ів
CB_PREFIX = 'menu:'

WELCOME_TEXT = 'Ласкаво просимо до бота профорієнтації університету! Оберіть пункт меню.'
