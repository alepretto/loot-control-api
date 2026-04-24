from uuid import UUID

from sqlmodel import Session, select

from app.models.transaction import Transaction


def get_by_id(session: Session, transaction_id: UUID) -> Transaction | None:
    return session.get(Transaction, transaction_id)


def get_all_by_user(session: Session, user_id: UUID) -> list[Transaction]:
    statement = select(Transaction).where(Transaction.user_id == user_id)
    return list(session.exec(statement).all())


def get_by_account(session: Session, user_id: UUID, account_id: UUID) -> list[Transaction]:
    statement = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .where(Transaction.account_id == account_id)
    )
    return list(session.exec(statement).all())


def get_by_statement(session: Session, user_id: UUID, statement_id: UUID) -> list[Transaction]:
    statement = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .where(Transaction.statement_id == statement_id)
    )
    return list(session.exec(statement).all())


def get_by_statement_raw(session: Session, statement_id: UUID) -> list[Transaction]:
    statement = select(Transaction).where(Transaction.statement_id == statement_id)
    return list(session.exec(statement).all())


def create(session: Session, transaction: Transaction) -> Transaction:
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def update(session: Session, transaction: Transaction) -> Transaction:
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def delete(session: Session, transaction: Transaction) -> None:
    session.delete(transaction)
    session.commit()
