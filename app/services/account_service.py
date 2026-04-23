from uuid import UUID

from sqlmodel import Session

from app.models.account import Account, AccountType
from app.repositories import account_repository


def create_account(
    session: Session,
    user_id: UUID,
    label: str,
    type: AccountType,
    logo: str | None = None,
) -> Account:
    account = Account(
        user_id=user_id,
        label=label,
        type=type,
        logo=logo,
    )
    return account_repository.create(session, account)


def list_accounts(session: Session, user_id: UUID) -> list[Account]:
    return account_repository.get_all_by_user(session, user_id)


def get_account_by_id(session: Session, account_id: UUID) -> Account:
    account = account_repository.get_by_id(session, account_id)
    if not account:
        raise ValueError("Account not found")
    return account


def update_account(
    session: Session,
    account_id: UUID,
    label: str | None = None,
    type: AccountType | None = None,
    logo: str | None = None,
) -> Account:
    account = account_repository.get_by_id(session, account_id)
    if not account:
        raise ValueError("Account not found")

    if label is not None:
        account.label = label
    if type is not None:
        account.type = type
    if logo is not None:
        account.logo = logo

    return account_repository.update(session, account)


def delete_account(session: Session, account_id: UUID) -> None:
    account = account_repository.get_by_id(session, account_id)
    if not account:
        raise ValueError("Account not found")
    account_repository.delete(session, account)
