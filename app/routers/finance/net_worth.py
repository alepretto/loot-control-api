import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.net_worth import NetWorthCurrent, NetWorthHistory
from app.services.finance.net_worth_service import NetWorthService

router = APIRouter(prefix="/finance/net-worth", tags=["net-worth"])


@router.get("/current", response_model=NetWorthCurrent)
async def get_current_net_worth(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await NetWorthService(session).get_current(uuid.UUID(current_user_id))


@router.get("/history", response_model=NetWorthHistory)
async def get_net_worth_history(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    months: int = Query(default=12, ge=1, le=60),
):
    snapshots = await NetWorthService(session).get_history(uuid.UUID(current_user_id), months)
    return NetWorthHistory(snapshots=snapshots)
