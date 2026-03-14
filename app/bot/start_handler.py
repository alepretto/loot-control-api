from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from app.core.config import settings
from app.core.database import engine
from app.models.user import User


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    telegram_id = str(update.effective_user.id)

    async with AsyncSession(engine) as session:
        result = await session.exec(select(User).where(User.telegram_id == telegram_id))
        user = result.first()

    if user:
        await update.message.reply_text(
            f"Olá, {user.first_name}! Pode me perguntar sobre seus gastos, investimentos ou resumo do mês."
        )
        return

    # Not linked yet — send button to open Mini App
    if settings.MINI_APP_URL:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Abrir Loot Control", web_app=WebAppInfo(url=settings.MINI_APP_URL))]
        ])
        await update.message.reply_text(
            "Para usar o bot, abra o app e faça o login:",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "Para usar o bot, faça o login no Loot Control e abra o Mini App pelo Telegram."
        )
