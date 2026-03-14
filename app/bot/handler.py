import logging
import uuid

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.agent import process_message
from app.core.config import settings
from app.core.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    if str(update.effective_user.id) != settings.TELEGRAM_USER_ID:
        await update.message.reply_text("Acesso não autorizado.")
        return

    user_id = uuid.UUID(settings.BOT_USER_ID)
    await update.message.chat.send_action("typing")

    try:
        async with AsyncSession(engine) as session:
            response = await process_message(session, user_id, update.message.text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        await update.message.reply_text("Ocorreu um erro ao processar sua mensagem. Tente novamente.")
