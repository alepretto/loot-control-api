from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services import transaction_service

router = APIRouter(tags=["Transactions"])


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    body: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        transaction = transaction_service.create_transaction(
            session,
            user_id=current_user.id,
            date_transaction=body.date_transaction,
            type=body.type,
            subcategory_id=body.subcategory_id,
            account_id=body.account_id,
            currency_id=body.currency_id,
            amount=body.amount,
            description=body.description,
            payment_methods=body.payment_methods,
            statement_id=body.statement_id,
            credit_card_id=body.credit_card_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return transaction


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    account_id: UUID | None = Query(None, description="Filter by account ID"),
    statement_id: UUID | None = Query(None, description="Filter by credit card statement ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if account_id:
        return transaction_service.list_transactions_by_account(session, user_id=current_user.id, account_id=account_id)
    if statement_id:
        return transaction_service.list_transactions_by_statement(session, user_id=current_user.id, statement_id=statement_id)
    return transaction_service.list_transactions(session, user_id=current_user.id)


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        transaction = transaction_service.get_transaction_by_id(session, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this transaction",
        )
    return transaction


@router.patch("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: UUID,
    body: TransactionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        transaction = transaction_service.get_transaction_by_id(session, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this transaction",
        )

    try:
        return transaction_service.update_transaction(
            session,
            transaction_id=transaction_id,
            date_transaction=body.date_transaction,
            type=body.type,
            subcategory_id=body.subcategory_id,
            account_id=body.account_id,
            currency_id=body.currency_id,
            description=body.description,
            amount=body.amount,
            payment_methods=body.payment_methods,
            statement_id=body.statement_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        transaction = transaction_service.get_transaction_by_id(session, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this transaction",
        )

    transaction_service.delete_transaction(session, transaction_id)
