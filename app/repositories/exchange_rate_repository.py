from datetime import date
from uuid import UUID

from sqlmodel import Session, select

from app.models.exchange_rate import ExchangeRate


def get_by_id(session: Session, rate_id: UUID) -> ExchangeRate | None:
    return session.get(ExchangeRate, rate_id)


def get_all(
    session: Session,
    from_currency: str | None = None,
    to_currency: str | None = None,
) -> list[ExchangeRate]:
    statement = select(ExchangeRate)
    if from_currency:
        statement = statement.where(ExchangeRate.from_currency == from_currency)
    if to_currency:
        statement = statement.where(ExchangeRate.to_currency == to_currency)
    statement = statement.order_by(ExchangeRate.rate_date.desc())
    return list(session.exec(statement).all())


def get_latest_rate(
    session: Session,
    from_currency: str,
    to_currency: str,
) -> ExchangeRate | None:
    statement = (
        select(ExchangeRate)
        .where(ExchangeRate.from_currency == from_currency)
        .where(ExchangeRate.to_currency == to_currency)
        .order_by(ExchangeRate.rate_date.desc())
        .limit(1)
    )
    return session.exec(statement).first()


def get_rate_on_date(
    session: Session,
    from_currency: str,
    to_currency: str,
    rate_date: date,
) -> ExchangeRate | None:
    statement = (
        select(ExchangeRate)
        .where(ExchangeRate.from_currency == from_currency)
        .where(ExchangeRate.to_currency == to_currency)
        .where(ExchangeRate.rate_date == rate_date)
    )
    return session.exec(statement).first()


def create(session: Session, rate_obj: ExchangeRate) -> ExchangeRate:
    session.add(rate_obj)
    session.commit()
    session.refresh(rate_obj)
    return rate_obj


def delete(session: Session, rate_obj: ExchangeRate) -> None:
    session.delete(rate_obj)
    session.commit()