from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.bot.handler import handle_message
from app.bot.start_handler import handle_start
from app.core.config import settings


def create_bot_app() -> Application:
    builder = Application.builder().token(settings.TELEGRAM_BOT_TOKEN)
    # Updater is only needed for polling; disable it when using webhooks
    if settings.WEBHOOK_URL:
        builder = builder.updater(None)
    app = builder.build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
