from uuid import UUID

from sqlmodel import Session

from app.models.currency import Currency
from app.repositories import currency_repository


def create_currency(
    session: Session,
    label: str,
    symbol: str,
) -> Currency:
    currency = Currency(
        label=label,
        symbol=symbol,
    )
    return currency_repository.create(session, currency)


def list_currencies(session: Session) -> list[Currency]:
    return currency_repository.get_all(session)


def get_currency_by_id(session: Session, currency_id: UUID) -> Currency:
    currency = currency_repository.get_by_id(session, currency_id)
    if not currency:
        raise ValueError("Currency not found")
    return currency


def update_currency(
    session: Session,
    currency_id: UUID,
    label: str | None = None,
    symbol: str | None = None,
) -> Currency:
    currency = currency_repository.get_by_id(session, currency_id)
    if not currency:
        raise ValueError("Currency not found")

    if label is not None:
        currency.label = label
    if symbol is not None:
        currency.symbol = symbol

    return currency_repository.update(session, currency)


def delete_currency(session: Session, currency_id: UUID) -> None:
    currency = currency_repository.get_by_id(session, currency_id)
    if not currency:
        raise ValueError("Currency not found")
    currency_repository.delete(session, currency)
