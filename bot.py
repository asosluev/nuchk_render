# bot.py
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)
from config import BOT_TOKEN, WEBHOOK_URL, PORT
from handlers.menu import start_menu, register_handlers as register_menu_handlers
from handlers.admin import register_handlers as register_admin_handlers

async def start_command(update: Update, context):
    await start_menu(update, context)

async def help_command(update: Update, context):
    await update.message.reply_text(
        "🤖 Бот університету\n\n"
        "/start — відкрити меню\n"
        "/help — ця довідка\n"
        "/reload — (адмін) перечитати JSON"
    )

async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # базові команди
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # підключаємо меню і адмін-хендлери
    register_menu_handlers(application)
    register_admin_handlers(application)

    # Налаштування aiohttp серверу для webhook
    async def health(request):
        return web.Response(text="OK")

    app = web.Application()
    # маршрут, який обробляє webhook POST від Telegram
    app.router.add_post("/webhook", application.webhook_handler)
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # встановлюємо webhook у Telegram
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print(f"Webhook set to: {WEBHOOK_URL}/webhook")
    print(f"Server started on 0.0.0.0:{PORT}")

    # додати graceful shutdown при потребі
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
