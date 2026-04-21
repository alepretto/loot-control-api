import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.budget import BudgetCreate, BudgetProgress, BudgetRead, BudgetUpdate
from app.services.finance.budget_service import BudgetService

router = APIRouter(prefix="/finance/budgets", tags=["budgets"])


@router.post("/", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
async def create_budget(
    data: BudgetCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await BudgetService(session).create(uuid.UUID(current_user_id), data)


@router.get("/progress", response_model=List[BudgetProgress])
async def get_budget_progress(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    month: str = Query(..., description="YYYY-MM"),
):
    return await BudgetService(session).get_progress(uuid.UUID(current_user_id), month)


@router.get("/", response_model=List[BudgetRead])
async def list_budgets(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    is_active: Optional[bool] = Query(default=None),
):
    return await BudgetService(session).list(uuid.UUID(current_user_id), is_active)


@router.get("/{budget_id}", response_model=BudgetRead)
async def get_budget(
    budget_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    budget = await BudgetService(session).get_by_id(budget_id, uuid.UUID(current_user_id))
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
    return budget


@router.patch("/{budget_id}", response_model=BudgetRead)
async def update_budget(
    budget_id: uuid.UUID,
    data: BudgetUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    budget = await BudgetService(session).update(budget_id, uuid.UUID(current_user_id), data)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await BudgetService(session).delete(budget_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
