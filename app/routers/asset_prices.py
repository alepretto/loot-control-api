from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.asset_price import AssetPriceCreate, AssetPriceResponse
from app.services import asset_price_service

router = APIRouter(tags=["Asset Prices"])


@router.post("/asset-prices", response_model=AssetPriceResponse, status_code=status.HTTP_201_CREATED)
def create_asset_price(
    body: AssetPriceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        asset_price = asset_price_service.create_asset_price(
            session,
            symbol=body.symbol,
            price_date=body.price_date,
            price=body.price,
            currency=body.currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return asset_price


@router.get("/asset-prices", response_model=list[AssetPriceResponse])
def list_asset_prices(
    symbol: str | None = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return asset_price_service.list_asset_prices(session, symbol=symbol)


@router.get("/asset-prices/latest", response_model=AssetPriceResponse)
def get_latest_asset_price(
    symbol: str = Query(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    asset_price = asset_price_service.get_latest_by_symbol(session, symbol)
    if not asset_price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for symbol '{symbol}'",
        )
    return asset_price


@router.get("/asset-prices/{price_id}", response_model=AssetPriceResponse)
def get_asset_price(
    price_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        asset_price = asset_price_service.get_by_id(session, price_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return asset_price


@router.delete("/asset-prices/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_price(
    price_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        asset_price_service.delete_asset_price(session, price_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))