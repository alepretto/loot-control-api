from uuid import UUID

from sqlmodel import Session, select

from app.models.currency import Currency


def get_by_id(session: Session, currency_id: UUID) -> Currency | None:
    return session.get(Currency, currency_id)


def get_all(session: Session) -> list[Currency]:
    statement = select(Currency)
    return list(session.exec(statement).all())


def create(session: Session, currency: Currency) -> Currency:
    session.add(currency)
    session.commit()
    session.refresh(currency)
    return currency


def update(session: Session, currency: Currency) -> Currency:
    session.add(currency)
    session.commit()
    session.refresh(currency)
    return currency


def delete(session: Session, currency: Currency) -> None:
    session.delete(currency)
    session.commit()
