import logging

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.agent import process_message
from app.core.database import engine
from app.models.user import User

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    telegram_id = str(update.effective_user.id)

    # Look up user by telegram_id
    async with AsyncSession(engine) as session:
        result = await session.exec(select(User).where(User.telegram_id == telegram_id))
        user = result.first()

    if not user:
        await update.message.reply_text("Sua conta não está vinculada. Acesse o app e faça o login pelo Telegram.")
        return

    await update.message.chat.send_action("typing")

    try:
        async with AsyncSession(engine) as session:
            response = await process_message(session, user.id, update.message.text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        await update.message.reply_text("Ocorreu um erro ao processar sua mensagem. Tente novamente.")
