import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import httpx

from app.core.config import settings

bearer_scheme = HTTPBearer()

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
            )
            resp.raise_for_status()
            _jwks_cache = resp.json()
    assert _jwks_cache is not None
    return _jwks_cache


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    try:
        jwks = await _get_jwks()
        payload = jwt.decode(
            credentials.credentials,
            jwks,
            algorithms=["ES256"],
            options={"verify_aud": False},
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return user_id
    except JWTError as e:
        print(f"[JWT ERROR] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def require_admin(
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> str:
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from sqlmodel import select

    async with AsyncSessionLocal() as session:
        result = await session.exec(select(User).where(User.id == uuid.UUID(current_user_id)))
        user = result.first()

    if not user or user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    return current_user_id
