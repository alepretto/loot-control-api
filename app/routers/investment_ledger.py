from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.investment_ledger import (
    InvestmentLedgerCreate,
    InvestmentLedgerResponse,
    InvestmentLedgerUpdate,
)
from app.services import investment_ledger_service

router = APIRouter(tags=["Investments"])


@router.post("/investments", response_model=InvestmentLedgerResponse, status_code=status.HTTP_201_CREATED)
def create_investment(
    body: InvestmentLedgerCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        investment = investment_ledger_service.create_investment(
            session,
            user_id=current_user.id,
            transaction_id=body.transaction_id,
            symbol=body.symbol,
            quantity=body.quantity,
            index=body.index,
            index_rate=body.index_rate,
            currency=body.currency,
            purchase_exchange_rate=body.purchase_exchange_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return investment


@router.get("/investments", response_model=list[InvestmentLedgerResponse])
def list_investments(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return investment_ledger_service.list_investments(session, user_id=current_user.id)


@router.get("/investments/portfolio")
def get_portfolio_summary(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return investment_ledger_service.get_portfolio_summary(session, current_user.id)


@router.get("/investments/portfolio/timeline")
def get_portfolio_timeline(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return investment_ledger_service.get_portfolio_timeline(
        session, current_user.id, start_date=start_date, end_date=end_date
    )


@router.get("/investments/{investment_id}", response_model=InvestmentLedgerResponse)
def get_investment(
    investment_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        investment = investment_ledger_service.get_investment_by_id(session, investment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if investment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this investment",
        )
    return investment


@router.patch("/investments/{investment_id}", response_model=InvestmentLedgerResponse)
def update_investment(
    investment_id: UUID,
    body: InvestmentLedgerUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        # Verify ownership
        investment = investment_ledger_service.get_investment_by_id(session, investment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if investment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this investment",
        )

    try:
        return investment_ledger_service.update_investment(
            session,
            ledger_id=investment_id,
            transaction_id=body.transaction_id,
            symbol=body.symbol,
            quantity=body.quantity,
            index=body.index,
            index_rate=body.index_rate,
            currency=body.currency,
            purchase_exchange_rate=body.purchase_exchange_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/investments/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
    investment_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        investment = investment_ledger_service.get_investment_by_id(session, investment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if investment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this investment",
        )

    investment_ledger_service.delete_investment(session, investment_id)
