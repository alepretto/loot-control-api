from uuid import UUID

from sqlmodel import Session, select

from app.models.credit_card_statement import CreditCardStatement


def get_by_id(session: Session, statement_id: UUID) -> CreditCardStatement | None:
    return session.get(CreditCardStatement, statement_id)


def get_all_by_user(session: Session, user_id: UUID) -> list[CreditCardStatement]:
    statement = select(CreditCardStatement).where(CreditCardStatement.user_id == user_id)
    return list(session.exec(statement).all())


def get_by_credit_card(session: Session, credit_card_id: UUID) -> list[CreditCardStatement]:
    statement = select(CreditCardStatement).where(CreditCardStatement.credit_card_id == credit_card_id)
    return list(session.exec(statement).all())


def create(session: Session, statement: CreditCardStatement) -> CreditCardStatement:
    session.add(statement)
    session.commit()
    session.refresh(statement)
    return statement


def update(session: Session, statement: CreditCardStatement) -> CreditCardStatement:
    session.add(statement)
    session.commit()
    session.refresh(statement)
    return statement


def delete(session: Session, statement: CreditCardStatement) -> None:
    session.delete(statement)
    session.commit()
