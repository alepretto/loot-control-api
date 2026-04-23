from uuid import UUID

from sqlmodel import Session

from app.models.subcategory import Subcategory
from app.repositories import subcategory_repository


def create_subcategory(
    session: Session,
    user_id: UUID,
    label: str,
    category_id: UUID,
    is_active: bool = True,
) -> Subcategory:
    subcategory = Subcategory(
        user_id=user_id,
        label=label,
        category_id=category_id,
        is_active=is_active,
    )
    return subcategory_repository.create(session, subcategory)


def list_subcategories(session: Session, user_id: UUID) -> list[Subcategory]:
    return subcategory_repository.get_all_by_user(session, user_id)


def get_subcategory_by_id(session: Session, subcategory_id: UUID) -> Subcategory:
    subcategory = subcategory_repository.get_by_id(session, subcategory_id)
    if not subcategory:
        raise ValueError("Subcategory not found")
    return subcategory


def update_subcategory(
    session: Session,
    subcategory_id: UUID,
    label: str | None = None,
    category_id: UUID | None = None,
    is_active: bool | None = None,
) -> Subcategory:
    subcategory = subcategory_repository.get_by_id(session, subcategory_id)
    if not subcategory:
        raise ValueError("Subcategory not found")

    if label is not None:
        subcategory.label = label
    if category_id is not None:
        subcategory.category_id = category_id
    if is_active is not None:
        subcategory.is_active = is_active

    return subcategory_repository.update(session, subcategory)


def delete_subcategory(session: Session, subcategory_id: UUID) -> None:
    subcategory = subcategory_repository.get_by_id(session, subcategory_id)
    if not subcategory:
        raise ValueError("Subcategory not found")
    subcategory_repository.delete(session, subcategory)
