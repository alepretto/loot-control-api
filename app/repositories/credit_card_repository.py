from uuid import UUID

from sqlmodel import Session, select

from app.models.credit_card import CreditCard


def get_by_id(session: Session, credit_card_id: UUID) -> CreditCard | None:
    return session.get(CreditCard, credit_card_id)


def get_all_by_user(session: Session, user_id: UUID) -> list[CreditCard]:
    statement = select(CreditCard).where(CreditCard.user_id == user_id)
    return list(session.exec(statement).all())


def create(session: Session, credit_card: CreditCard) -> CreditCard:
    session.add(credit_card)
    session.commit()
    session.refresh(credit_card)
    return credit_card


def update(session: Session, credit_card: CreditCard) -> CreditCard:
    session.add(credit_card)
    session.commit()
    session.refresh(credit_card)
    return credit_card


def delete(session: Session, credit_card: CreditCard) -> None:
    session.delete(credit_card)
    session.commit()