from uuid import UUID

from sqlmodel import Session, select

from app.models.account import Account


def get_by_id(session: Session, account_id: UUID) -> Account | None:
    return session.get(Account, account_id)


def get_all_by_user(session: Session, user_id: UUID) -> list[Account]:
    statement = select(Account).where(Account.user_id == user_id)
    return list(session.exec(statement).all())


def create(session: Session, account: Account) -> Account:
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def update(session: Session, account: Account) -> Account:
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def delete(session: Session, account: Account) -> None:
    session.delete(account)
    session.commit()