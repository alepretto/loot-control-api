import logging

from fastapi import APIRouter, HTTPException, Request, status
from telegram import Update

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bot"])


@router.post("/bot/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """Receive updates from Telegram via webhook."""
    if token != settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    import app.bot.state as bot_state
    if bot_state.bot_app is None:
        return {"ok": False}

    data = await request.json()
    update = Update.de_json(data, bot_state.bot_app.bot)
    await bot_state.bot_app.process_update(update)
    return {"ok": True}
