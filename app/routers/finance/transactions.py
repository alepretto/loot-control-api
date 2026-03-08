import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.finance.transaction import Currencies
from app.schemas.finance.transaction import (
    TransactionCreate,
    TransactionFilter,
    TransactionRead,
    TransactionUpdate,
)
from app.services.finance.transaction_service import TransactionService

router = APIRouter(prefix="/finance/transactions", tags=["transactions"])


class PaginatedTransactions(BaseModel):
    items: List[TransactionRead]
    total: int
    page: int
    page_size: int


@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await TransactionService(session).create(uuid.UUID(current_user_id), data)


@router.get("/", response_model=PaginatedTransactions)
async def list_transactions(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    tag_id: Optional[uuid.UUID] = Query(default=None),
    currency: Optional[Currencies] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=200),
):
    filters = TransactionFilter(
        tag_id=tag_id,
        currency=currency,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        page=page,
        page_size=page_size,
    )
    items, total = await TransactionService(session).list(uuid.UUID(current_user_id), filters)
    return PaginatedTransactions(items=items, total=total, page=page, page_size=page_size)


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    transaction_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    tx = await TransactionService(session).get_by_id(transaction_id, uuid.UUID(current_user_id))
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    transaction_id: uuid.UUID,
    data: TransactionUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    tx = await TransactionService(session).update(
        transaction_id, uuid.UUID(current_user_id), data
    )
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await TransactionService(session).delete(
        transaction_id, uuid.UUID(current_user_id)
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
