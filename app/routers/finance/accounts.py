import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.account import AccountCreate, AccountReadWithBalance, AccountUpdate
from app.schemas.finance.transaction import TransactionRead
from app.services.finance.account_service import AccountService

router = APIRouter(prefix="/finance/accounts", tags=["accounts"])


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date format: {value}")


class PaginatedTransactions(BaseModel):
    items: List[TransactionRead]
    total: int
    page: int
    page_size: int


@router.post("/", response_model=AccountReadWithBalance, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    svc = AccountService(session)
    account = await svc.create(uuid.UUID(current_user_id), data)
    return await svc.calculate_balance(account)


@router.get("/", response_model=List[AccountReadWithBalance])
async def list_accounts(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    is_active: Optional[bool] = Query(default=None),
):
    svc = AccountService(session)
    accounts = await svc.list(uuid.UUID(current_user_id), is_active)
    return [await svc.calculate_balance(a) for a in accounts]


@router.get("/{account_id}", response_model=AccountReadWithBalance)
async def get_account(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    svc = AccountService(session)
    account = await svc.get_by_id(account_id, uuid.UUID(current_user_id))
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    return await svc.calculate_balance(account)


@router.patch("/{account_id}", response_model=AccountReadWithBalance)
async def update_account(
    account_id: uuid.UUID,
    data: AccountUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    svc = AccountService(session)
    account = await svc.update(account_id, uuid.UUID(current_user_id), data)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    return await svc.calculate_balance(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await AccountService(session).delete(account_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")


@router.get("/{account_id}/statement", response_model=PaginatedTransactions)
async def get_statement(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=2000),
):
    items, total = await AccountService(session).get_statement(
        account_id,
        uuid.UUID(current_user_id),
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
        page=page,
        page_size=page_size,
    )
    return PaginatedTransactions(items=items, total=total, page=page, page_size=page_size)
