from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.bot.handler import handle_message
from app.bot.start_handler import handle_start
from app.core.config import settings


def create_bot_app() -> Application:
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
