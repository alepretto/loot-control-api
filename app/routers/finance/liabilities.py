import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.liability import LiabilityCreate, LiabilityRead, LiabilityUpdate
from app.services.finance.liability_service import LiabilityService

router = APIRouter(prefix="/finance/liabilities", tags=["liabilities"])


@router.post("/", response_model=LiabilityRead, status_code=status.HTTP_201_CREATED)
async def create_liability(
    data: LiabilityCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await LiabilityService(session).create(uuid.UUID(current_user_id), data)


@router.get("/", response_model=List[LiabilityRead])
async def list_liabilities(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    is_active: Optional[bool] = Query(default=None),
):
    return await LiabilityService(session).list(uuid.UUID(current_user_id), is_active)


@router.get("/{liability_id}", response_model=LiabilityRead)
async def get_liability(
    liability_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    liability = await LiabilityService(session).get_by_id(liability_id, uuid.UUID(current_user_id))
    if not liability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passivo não encontrado")
    return liability


@router.patch("/{liability_id}", response_model=LiabilityRead)
async def update_liability(
    liability_id: uuid.UUID,
    data: LiabilityUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    liability = await LiabilityService(session).update(liability_id, uuid.UUID(current_user_id), data)
    if not liability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passivo não encontrado")
    return liability


@router.delete("/{liability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_liability(
    liability_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await LiabilityService(session).delete(liability_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passivo não encontrado")
