import uuid
from datetime import UTC, datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.finance.tag_family import FamilyNature
from app.models.finance.transaction import Currencies
from app.schemas.finance.transaction import (
    TransactionCreate,
    TransactionFilter,
    TransactionRead,
    TransactionUpdate,
)
from app.services.finance.summary_service import SummaryService
from app.services.finance.transaction_service import TransactionService

router = APIRouter(prefix="/finance/transactions", tags=["transactions"])


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


# 1. POST - create
@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await TransactionService(session).create(uuid.UUID(current_user_id), data)


# 2. GET / - list
@router.get("/", response_model=PaginatedTransactions)
async def list_transactions(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    tag_id: Optional[uuid.UUID] = Query(default=None),
    category_id: Optional[uuid.UUID] = Query(default=None),
    family_id: Optional[uuid.UUID] = Query(default=None),
    nature: Optional[FamilyNature] = Query(default=None),
    currency: Optional[Currencies] = Query(default=None),
    account_id: Optional[uuid.UUID] = Query(default=None),
    invoice_id: Optional[uuid.UUID] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=2000),
):
    filters = TransactionFilter(
        tag_id=tag_id,
        category_id=category_id,
        family_id=family_id,
        nature=nature,
        currency=currency,
        account_id=account_id,
        invoice_id=invoice_id,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
        page=page,
        page_size=page_size,
    )
    items, total = await TransactionService(session).list(uuid.UUID(current_user_id), filters)
    return PaginatedTransactions(items=items, total=total, page=page, page_size=page_size)


# 3. GET /summary - summary (MUST be before /{transaction_id})
@router.get("/summary")
async def get_transactions_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    month: Optional[str] = Query(default=None, description="YYYY-MM"),
):
    if month:
        try:
            year_val, month_val = int(month[:4]), int(month[5:7])
        except (ValueError, IndexError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month format. Use YYYY-MM")
    else:
        today = datetime.now(UTC)
        year_val, month_val = today.year, today.month
    summary = await SummaryService().get_monthly_summary(
        session, uuid.UUID(current_user_id), month_val, year_val
    )
    return {
        "month": summary.get("month"),
        "year": summary.get("year"),
        "total_income": float(summary.get("total_income", 0)),
        "total_fixed_expense": float(summary.get("total_fixed_expense", 0)),
        "total_variable_expense": float(summary.get("total_variable_expense", 0)),
        "total_investment": float(summary.get("total_investment", 0)),
        "total_expense": float(summary.get("total_expense", 0)),
        "balance": float(summary.get("balance", 0)),
        "saving_rate": float(summary.get("saving_rate", 0)),
        "income_by_type": summary.get("income_by_type", {}),
        "by_family": summary.get("by_family", {}),
        "top_tags": summary.get("top_tags", []),
        "has_foreign_currency": bool(summary.get("has_foreign_currency", False)),
    }


# 4. GET /{transaction_id} - get one
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


# 5. PATCH /{transaction_id} - update
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


# 6. DELETE /{transaction_id} - delete
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