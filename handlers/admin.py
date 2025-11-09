# handlers/admin.py
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import ADMIN_IDS
from handlers.menu import menu_manager

async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Лише для адміністратора.")
        return
    try:
        menu_manager.load()
        await update.message.reply_text("♻️ Дані меню перезавантажено.")
    except Exception as e:
        await update.message.reply_text(f"❌ Помилка при перезавантаженні: {e}")

def register_handlers(application):
    application.add_handler(CommandHandler("reload", reload_command))
