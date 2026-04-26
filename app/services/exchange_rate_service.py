from datetime import date
from uuid import UUID

from sqlmodel import Session

from app.models.exchange_rate import ExchangeRate
from app.repositories import exchange_rate_repository


def create_exchange_rate(
    session: Session,
    from_currency: str,
    to_currency: str,
    rate_date: date,
    rate: float,
) -> ExchangeRate:
    existing = exchange_rate_repository.get_rate_on_date(session, from_currency, to_currency, rate_date)
    if existing:
        existing.rate = rate
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    exchange_rate = ExchangeRate(
        from_currency=from_currency,
        to_currency=to_currency,
        rate_date=rate_date,
        rate=rate,
    )
    return exchange_rate_repository.create(session, exchange_rate)


def list_exchange_rates(
    session: Session,
    from_currency: str | None = None,
    to_currency: str | None = None,
) -> list[ExchangeRate]:
    return exchange_rate_repository.get_all(
        session,
        from_currency=from_currency,
        to_currency=to_currency,
    )


def get_latest_rate(
    session: Session,
    from_currency: str,
    to_currency: str,
) -> ExchangeRate:
    rate = exchange_rate_repository.get_latest_rate(session, from_currency, to_currency)
    if not rate:
        raise ValueError("Exchange rate not found")
    return rate


def get_rate_on_date(
    session: Session,
    from_currency: str,
    to_currency: str,
    rate_date: date,
) -> ExchangeRate:
    rate = exchange_rate_repository.get_rate_on_date(
        session, from_currency, to_currency, rate_date
    )
    if not rate:
        raise ValueError("Exchange rate not found for the given date")
    return rate


def get_by_id(session: Session, rate_id: UUID) -> ExchangeRate:
    rate = exchange_rate_repository.get_by_id(session, rate_id)
    if not rate:
        raise ValueError("Exchange rate not found")
    return rate


def delete_exchange_rate(session: Session, rate_id: UUID) -> None:
    rate = exchange_rate_repository.get_by_id(session, rate_id)
    if not rate:
        raise ValueError("Exchange rate not found")
    exchange_rate_repository.delete(session, rate)