import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.recurrence_rule import RecurrenceRuleCreate, RecurrenceRuleRead, RecurrenceRuleUpdate
from app.services.finance.recurrence_rule_service import RecurrenceRuleService

router = APIRouter(prefix="/finance/recurrences", tags=["recurrences"])


@router.post("/", response_model=RecurrenceRuleRead, status_code=status.HTTP_201_CREATED)
async def create_recurrence(
    data: RecurrenceRuleCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await RecurrenceRuleService(session).create(uuid.UUID(current_user_id), data)


@router.get("/", response_model=List[RecurrenceRuleRead])
async def list_recurrences(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    is_active: Optional[bool] = Query(default=None),
):
    return await RecurrenceRuleService(session).list(uuid.UUID(current_user_id), is_active)


@router.get("/{rule_id}", response_model=RecurrenceRuleRead)
async def get_recurrence(
    rule_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    rule = await RecurrenceRuleService(session).get_by_id(rule_id, uuid.UUID(current_user_id))
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recorrência não encontrada")
    return rule


@router.patch("/{rule_id}", response_model=RecurrenceRuleRead)
async def update_recurrence(
    rule_id: uuid.UUID,
    data: RecurrenceRuleUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    rule = await RecurrenceRuleService(session).update(rule_id, uuid.UUID(current_user_id), data)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recorrência não encontrada")
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurrence(
    rule_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await RecurrenceRuleService(session).delete(rule_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recorrência não encontrada")
