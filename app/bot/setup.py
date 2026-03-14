from telegram.ext import Application, MessageHandler, filters

from app.bot.handler import handle_message
from app.core.config import settings


def create_bot_app() -> Application:
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
