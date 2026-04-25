from datetime import date
from uuid import UUID

from sqlmodel import Session, select

from app.models.asset_price import AssetPrice


def get_by_id(session: Session, price_id: UUID) -> AssetPrice | None:
    return session.get(AssetPrice, price_id)


def get_all(session: Session, symbol: str | None = None) -> list[AssetPrice]:
    if symbol:
        statement = select(AssetPrice).where(AssetPrice.symbol == symbol).order_by(AssetPrice.price_date.desc())
    else:
        statement = select(AssetPrice).order_by(AssetPrice.price_date.desc())
    return list(session.exec(statement).all())


def get_latest_by_symbol(session: Session, symbol: str) -> AssetPrice | None:
    statement = (
        select(AssetPrice)
        .where(AssetPrice.symbol == symbol)
        .order_by(AssetPrice.price_date.desc())
        .limit(1)
    )
    return session.exec(statement).first()


def get_by_symbol_and_date(session: Session, symbol: str, price_date: date) -> AssetPrice | None:
    statement = select(AssetPrice).where(
        AssetPrice.symbol == symbol,
        AssetPrice.price_date == price_date,
    )
    return session.exec(statement).first()


def create(session: Session, price: AssetPrice) -> AssetPrice:
    session.add(price)
    session.commit()
    session.refresh(price)
    return price


def delete(session: Session, price: AssetPrice) -> None:
    session.delete(price)
    session.commit()