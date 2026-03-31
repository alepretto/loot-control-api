import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.payment_method import (
    PaymentMethodCreate,
    PaymentMethodRead,
    PaymentMethodUpdate,
)
from app.services.finance.payment_method_service import PaymentMethodService

router = APIRouter(prefix="/finance/payment-methods", tags=["payment-methods"])


@router.post("/", response_model=PaymentMethodRead, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    data: PaymentMethodCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await PaymentMethodService(session).create(uuid.UUID(current_user_id), data)


@router.get("/", response_model=List[PaymentMethodRead])
async def list_payment_methods(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    is_active: Optional[bool] = Query(default=None),
):
    return await PaymentMethodService(session).list(uuid.UUID(current_user_id), is_active=is_active)


@router.get("/{pm_id}", response_model=PaymentMethodRead)
async def get_payment_method(
    pm_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    pm = await PaymentMethodService(session).get_by_id(pm_id, uuid.UUID(current_user_id))
    if not pm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Método de pagamento não encontrado")
    return pm


@router.patch("/{pm_id}", response_model=PaymentMethodRead)
async def update_payment_method(
    pm_id: uuid.UUID,
    data: PaymentMethodUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    pm = await PaymentMethodService(session).update(pm_id, uuid.UUID(current_user_id), data)
    if not pm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Método de pagamento não encontrado")
    return pm


@router.delete("/{pm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    pm_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await PaymentMethodService(session).delete(pm_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Método de pagamento não encontrado")
