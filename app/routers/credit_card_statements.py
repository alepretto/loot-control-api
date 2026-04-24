from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.credit_card_statement import (
    CreditCardStatementCreate,
    CreditCardStatementResponse,
    CreditCardStatementUpdate,
)
from app.services import credit_card_statement_service

router = APIRouter(tags=["Credit Card Statements"])


@router.post("/credit-card-statements", response_model=CreditCardStatementResponse, status_code=status.HTTP_201_CREATED)
def create_statement(
    body: CreditCardStatementCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        statement = credit_card_statement_service.create_statement(
            session,
            user_id=current_user.id,
            credit_card_id=body.credit_card_id,
            end_date=body.end_date,
            is_paid=body.is_paid,
            total_amount=body.total_amount,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return statement


@router.get("/credit-card-statements", response_model=list[CreditCardStatementResponse])
def list_statements(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return credit_card_statement_service.list_statements(session, user_id=current_user.id)


@router.get("/credit-card-statements/{statement_id}", response_model=CreditCardStatementResponse)
def get_statement(
    statement_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        statement = credit_card_statement_service.get_statement_by_id(session, statement_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if statement.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this statement",
        )
    return statement


@router.patch("/credit-card-statements/{statement_id}", response_model=CreditCardStatementResponse)
def update_statement(
    statement_id: UUID,
    body: CreditCardStatementUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        # Verify ownership
        statement = credit_card_statement_service.get_statement_by_id(session, statement_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if statement.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this statement",
        )

    try:
        return credit_card_statement_service.update_statement(
            session,
            statement_id=statement_id,
            end_date=body.end_date,
            is_paid=body.is_paid,
            total_amount=body.total_amount,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/credit-card-statements/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_statement(
    statement_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        statement = credit_card_statement_service.get_statement_by_id(session, statement_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if statement.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this statement",
        )

    credit_card_statement_service.delete_statement(session, statement_id)
