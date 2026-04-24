from uuid import UUID

from sqlmodel import Session

from app.models.credit_card import CreditCard
from app.repositories import credit_card_repository


def create_credit_card(
    session: Session,
    user_id: UUID,
    account_id: UUID,
    label: str,
    due_date: int,
    end_date_offset: int,
    is_active: bool = True,
) -> CreditCard:
    credit_card = CreditCard(
        user_id=user_id,
        account_id=account_id,
        label=label,
        due_date=due_date,
        end_date_offset=end_date_offset,
        is_active=is_active,
    )
    return credit_card_repository.create(session, credit_card)


def list_credit_cards(session: Session, user_id: UUID) -> list[CreditCard]:
    return credit_card_repository.get_all_by_user(session, user_id)


def get_credit_card_by_id(session: Session, credit_card_id: UUID) -> CreditCard:
    credit_card = credit_card_repository.get_by_id(session, credit_card_id)
    if not credit_card:
        raise ValueError("Credit card not found")
    return credit_card


def update_credit_card(
    session: Session,
    credit_card_id: UUID,
    account_id: UUID | None = None,
    label: str | None = None,
    due_date: int | None = None,
    end_date_offset: int | None = None,
    is_active: bool | None = None,
) -> CreditCard:
    credit_card = credit_card_repository.get_by_id(session, credit_card_id)
    if not credit_card:
        raise ValueError("Credit card not found")

    if account_id is not None:
        credit_card.account_id = account_id
    if label is not None:
        credit_card.label = label
    if due_date is not None:
        credit_card.due_date = due_date
    if end_date_offset is not None:
        credit_card.end_date_offset = end_date_offset
    if is_active is not None:
        credit_card.is_active = is_active

    return credit_card_repository.update(session, credit_card)


def delete_credit_card(session: Session, credit_card_id: UUID) -> None:
    credit_card = credit_card_repository.get_by_id(session, credit_card_id)
    if not credit_card:
        raise ValueError("Credit card not found")
    credit_card_repository.delete(session, credit_card)