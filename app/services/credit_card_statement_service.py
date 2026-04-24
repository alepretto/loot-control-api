from datetime import datetime
from uuid import UUID

from sqlmodel import Session

from app.models.credit_card_statement import CreditCardStatement
from app.repositories import credit_card_statement_repository


def create_statement(
    session: Session,
    user_id: UUID,
    credit_card_id: UUID,
    end_date: datetime,
    is_paid: bool = False,
    total_amount: float | None = None,
) -> CreditCardStatement:
    statement = CreditCardStatement(
        user_id=user_id,
        credit_card_id=credit_card_id,
        end_date=end_date,
        is_paid=is_paid,
        total_amount=total_amount,
    )
    return credit_card_statement_repository.create(session, statement)


def list_statements(session: Session, user_id: UUID) -> list[CreditCardStatement]:
    return credit_card_statement_repository.get_all_by_user(session, user_id)


def get_statement_by_id(session: Session, statement_id: UUID) -> CreditCardStatement:
    statement = credit_card_statement_repository.get_by_id(session, statement_id)
    if not statement:
        raise ValueError("Statement not found")
    return statement


def update_statement(
    session: Session,
    statement_id: UUID,
    end_date: datetime | None = None,
    is_paid: bool | None = None,
    total_amount: float | None = None,
) -> CreditCardStatement:
    statement = credit_card_statement_repository.get_by_id(session, statement_id)
    if not statement:
        raise ValueError("Statement not found")

    if end_date is not None:
        statement.end_date = end_date
    if is_paid is not None:
        statement.is_paid = is_paid
    if total_amount is not None:
        statement.total_amount = total_amount

    return credit_card_statement_repository.update(session, statement)


def delete_statement(session: Session, statement_id: UUID) -> None:
    statement = credit_card_statement_repository.get_by_id(session, statement_id)
    if not statement:
        raise ValueError("Statement not found")
    credit_card_statement_repository.delete(session, statement)
