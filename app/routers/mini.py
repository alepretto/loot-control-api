import hashlib
import hmac
import uuid
from typing import Annotated
from urllib.parse import parse_qsl, unquote

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.services.user_service import UserService

router = APIRouter(prefix="/mini", tags=["mini"])


class TelegramAuthRequest(BaseModel):
    init_data: str  # raw initData string from Telegram.WebApp.initData


def _verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Validate Telegram Mini App initData using HMAC-SHA256.
    Returns parsed fields if valid, raises HTTPException if invalid.
    """
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = params.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing hash in initData")

    # Build data-check-string: sorted key=value pairs joined by \n
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

    # Secret key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(received_hash, expected_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram initData signature")

    return params


@router.post("/auth/telegram", status_code=status.HTTP_200_OK)
async def link_telegram(
    body: TelegramAuthRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    """
    Validate Telegram Mini App initData and save the user's telegram_id (chat_id).
    Called once when the Mini App loads to link the authenticated user to their Telegram account.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram bot not configured")

    params = _verify_telegram_init_data(body.init_data, settings.TELEGRAM_BOT_TOKEN)

    # Extract user.id from the "user" JSON field
    import json
    user_json = params.get("user")
    if not user_json:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user data in initData")

    telegram_user = json.loads(unquote(user_json))
    telegram_id = str(telegram_user.get("id"))
    if not telegram_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user id in Telegram data")

    from app.schemas.user import UserUpdate
    user = await UserService(session).update(uuid.UUID(current_user_id), UserUpdate(telegram_id=telegram_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"linked": True, "telegram_id": telegram_id}
