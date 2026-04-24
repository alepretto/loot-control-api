from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.credit_card import (
    CreditCardCreate,
    CreditCardResponse,
    CreditCardUpdate,
)
from app.services import credit_card_service

router = APIRouter(tags=["Credit Cards"])


@router.post("/credit-cards", response_model=CreditCardResponse, status_code=status.HTTP_201_CREATED)
def create_credit_card(
    body: CreditCardCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        credit_card = credit_card_service.create_credit_card(
            session,
            user_id=current_user.id,
            account_id=body.account_id,
            label=body.label,
            due_date=body.due_date,
            end_date_offset=body.end_date_offset,
            is_active=body.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return credit_card


@router.get("/credit-cards", response_model=list[CreditCardResponse])
def list_credit_cards(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return credit_card_service.list_credit_cards(session, user_id=current_user.id)


@router.get("/credit-cards/{credit_card_id}", response_model=CreditCardResponse)
def get_credit_card(
    credit_card_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        credit_card = credit_card_service.get_credit_card_by_id(session, credit_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if credit_card.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this credit card",
        )
    return credit_card


@router.patch("/credit-cards/{credit_card_id}", response_model=CreditCardResponse)
def update_credit_card(
    credit_card_id: UUID,
    body: CreditCardUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        # Verify ownership
        credit_card = credit_card_service.get_credit_card_by_id(session, credit_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if credit_card.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this credit card",
        )

    try:
        return credit_card_service.update_credit_card(
            session,
            credit_card_id=credit_card_id,
            account_id=body.account_id,
            label=body.label,
            due_date=body.due_date,
            end_date_offset=body.end_date_offset,
            is_active=body.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/credit-cards/{credit_card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credit_card(
    credit_card_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        credit_card = credit_card_service.get_credit_card_by_id(session, credit_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if credit_card.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this credit card",
        )

    credit_card_service.delete_credit_card(session, credit_card_id)