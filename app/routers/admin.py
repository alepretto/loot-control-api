from datetime import date, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import require_admin
from app.models.user import User
from app.services import exchange_rate_service

router = APIRouter(tags=["Admin"])

AWESOME_API_BASE = "https://economia.awesomeapi.com.br/json"


class UpdateExchangeRatesRequest(BaseModel):
    from_currency: str = "USD"
    to_currency: str = "BRL"
    start_date: date
    end_date: date


class UpdateExchangeRatesResponse(BaseModel):
    total_processed: int
    from_currency: str
    to_currency: str
    start_date: str
    end_date: str
    days_requested: int


def _parse_awesome_date(dt_str: str) -> date:
    """Parse AwesomeAPI create_date format like '2026-04-25 10:00:00'."""
    return datetime.strptime(dt_str.split(".")[0], "%Y-%m-%d %H:%M:%S").date()


@router.post(
    "/admin/update-exchange-rates",
    response_model=UpdateExchangeRatesResponse,
    status_code=status.HTTP_200_OK,
)
def update_exchange_rates(
    body: UpdateExchangeRatesRequest,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    """Fetch exchange rates from AwesomeAPI for a date range and upsert them."""
    if body.start_date > body.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )

    days = (body.end_date - body.start_date).days + 1
    # Clamp to a reasonable max — AwesomeAPI supports up to ~365 days
    days = min(days, 365)

    from_code = body.from_currency.upper()
    to_code = body.to_currency.upper()

    url = (
        f"{AWESOME_API_BASE}/daily/"
        f"{from_code}-{to_code}/{days}"
        f"?start_date={body.start_date.strftime('%Y%m%d')}"
        f"&end_date={body.end_date.strftime('%Y%m%d')}"
    )

    try:
        response = httpx.get(url, timeout=30)
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch exchange rates from AwesomeAPI: {str(e)}",
        )

    total_processed = 0

    for item in data:
        try:
            rate_date = _parse_awesome_date(item["create_date"])
            rate = float(item["bid"])
        except (KeyError, ValueError, TypeError):
            continue

        # Service handles upsert (creates or updates) internally
        exchange_rate_service.create_exchange_rate(
            session, from_currency=from_code, to_currency=to_code,
            rate_date=rate_date, rate=rate,
        )
        total_processed += 1

    return UpdateExchangeRatesResponse(
        total_processed=total_processed,
        from_currency=from_code,
        to_currency=to_code,
        start_date=body.start_date.isoformat(),
        end_date=body.end_date.isoformat(),
        days_requested=days,
    )
