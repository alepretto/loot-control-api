from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.currency import CurrencyCreate, CurrencyResponse, CurrencyUpdate
from app.services import currency_service

router = APIRouter(tags=["Currencies"])


@router.post(
    "/currencies", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED
)
def create_currency(
    body: CurrencyCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        currency = currency_service.create_currency(
            session,
            label=body.label,
            symbol=body.symbol,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return currency


@router.get("/currencies", response_model=list[CurrencyResponse])
def list_currencies(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return currency_service.list_currencies(session)


@router.get("/currencies/{currency_id}", response_model=CurrencyResponse)
def get_currency(
    currency_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        currency = currency_service.get_currency_by_id(session, currency_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return currency


@router.patch("/currencies/{currency_id}", response_model=CurrencyResponse)
def update_currency(
    currency_id: UUID,
    body: CurrencyUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return currency_service.update_currency(
            session,
            currency_id=currency_id,
            label=body.label,
            symbol=body.symbol,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/currencies/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(
    currency_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        currency_service.delete_currency(session, currency_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
