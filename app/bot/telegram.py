import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_message(text: str, parse_mode: str = "Markdown") -> None:
    """Send a message to the configured Telegram user."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_USER_ID:
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json={
                "chat_id": settings.TELEGRAM_USER_ID,
                "text": text,
                "parse_mode": parse_mode,
            })
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
