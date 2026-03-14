import logging
import uuid

import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_message_to_user(session: AsyncSession, user_id: uuid.UUID, text: str, parse_mode: str = "Markdown") -> None:
    """Send a Telegram message to a specific user. Skips silently if user has no telegram_id."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    from app.models.user import User
    result = await session.exec(select(User.telegram_id).where(User.id == user_id))
    telegram_id = result.first()

    if not telegram_id:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json={
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": parse_mode,
            })
    except Exception as e:
        logger.error(f"Failed to send Telegram message to user {user_id}: {e}")
