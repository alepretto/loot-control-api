from datetime import date
from uuid import UUID

from sqlmodel import Session

from app.models.asset_price import AssetPrice
from app.repositories import asset_price_repository


def create_asset_price(
    session: Session,
    symbol: str,
    price_date: date,
    price: float,
    currency: str = "BRL",
) -> AssetPrice:
    existing = asset_price_repository.get_by_symbol_and_date(session, symbol, price_date)
    if existing:
        existing.price = price
        existing.currency = currency
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    asset_price = AssetPrice(
        symbol=symbol,
        price_date=price_date,
        price=price,
        currency=currency,
    )
    return asset_price_repository.create(session, asset_price)


def list_asset_prices(session: Session, symbol: str | None = None) -> list[AssetPrice]:
    return asset_price_repository.get_all(session, symbol=symbol)


def get_latest_by_symbol(session: Session, symbol: str) -> AssetPrice | None:
    return asset_price_repository.get_latest_by_symbol(session, symbol)


def get_by_id(session: Session, price_id: UUID) -> AssetPrice:
    asset_price = asset_price_repository.get_by_id(session, price_id)
    if not asset_price:
        raise ValueError("Asset price not found")
    return asset_price


def delete_asset_price(session: Session, price_id: UUID) -> None:
    asset_price = asset_price_repository.get_by_id(session, price_id)
    if not asset_price:
        raise ValueError("Asset price not found")
    asset_price_repository.delete(session, asset_price)