import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.credit_card import CreditCardCreate, CreditCardRead, CreditCardUpdate
from app.services.finance.credit_card_service import CreditCardService

router = APIRouter(prefix="/finance/credit-cards", tags=["credit-cards"])


@router.post("/", response_model=CreditCardRead, status_code=status.HTTP_201_CREATED)
async def create_credit_card(
    data: CreditCardCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await CreditCardService(session).create(
        uuid.UUID(current_user_id), data
    )


@router.get("/", response_model=List[CreditCardRead])
async def list_credit_cards(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    is_active: Optional[bool] = Query(default=None),
):
    return await CreditCardService(session).list(
        uuid.UUID(current_user_id), is_active
    )


@router.get("/{card_id}", response_model=CreditCardRead)
async def get_credit_card(
    card_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    card = await CreditCardService(session).get_by_id(
        uuid.UUID(card_id), uuid.UUID(current_user_id)
    )
    if not card:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")
    return card


@router.patch("/{card_id}", response_model=CreditCardRead)
async def update_credit_card(
    card_id: str,
    data: CreditCardUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    card = await CreditCardService(session).update(
        uuid.UUID(card_id), uuid.UUID(current_user_id), data
    )
    if not card:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credit_card(
    card_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await CreditCardService(session).delete(
        uuid.UUID(card_id), uuid.UUID(current_user_id)
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")