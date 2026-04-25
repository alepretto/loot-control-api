from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateResponse
from app.services import exchange_rate_service

router = APIRouter(tags=["Exchange Rates"])


@router.post(
    "/exchange-rates",
    response_model=ExchangeRateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_exchange_rate(
    body: ExchangeRateCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        exchange_rate = exchange_rate_service.create_exchange_rate(
            session,
            from_currency=body.from_currency,
            to_currency=body.to_currency,
            rate_date=body.rate_date,
            rate=body.rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return exchange_rate


@router.get("/exchange-rates", response_model=list[ExchangeRateResponse])
def list_exchange_rates(
    from_currency: str | None = Query(None),
    to_currency: str | None = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return exchange_rate_service.list_exchange_rates(
        session, from_currency=from_currency, to_currency=to_currency
    )


@router.get("/exchange-rates/latest", response_model=ExchangeRateResponse)
def get_latest_rate(
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return exchange_rate_service.get_latest_rate(session, from_currency, to_currency)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/exchange-rates/on-date", response_model=ExchangeRateResponse)
def get_rate_on_date(
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    rate_date: date = Query(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return exchange_rate_service.get_rate_on_date(
            session, from_currency, to_currency, rate_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/exchange-rates/{rate_id}", response_model=ExchangeRateResponse)
def get_exchange_rate(
    rate_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return exchange_rate_service.get_by_id(session, rate_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/exchange-rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exchange_rate(
    rate_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        exchange_rate_service.delete_exchange_rate(session, rate_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))