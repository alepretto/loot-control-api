from uuid import UUID

from sqlmodel import Session, select

from app.models.category import Category
from app.models.category import CategoryNature
from app.models.subcategory import Subcategory
from app.repositories import category_repository


def create_category(
    session: Session,
    user_id: UUID,
    label: str,
    nature: CategoryNature,
) -> Category:
    existing = category_repository.get_by_user_and_label(session, user_id, label)
    if existing:
        raise ValueError("Category with this name already exists")

    category = Category(
        user_id=user_id,
        label=label,
        nature=nature,
    )
    return category_repository.create(session, category)


def list_categories(session: Session, user_id: UUID) -> list[Category]:
    return category_repository.get_all_by_user(session, user_id)


def get_category_by_id(session: Session, category_id: UUID) -> Category:
    category = category_repository.get_by_id(session, category_id)
    if not category:
        raise ValueError("Category not found")
    return category


def update_category(
    session: Session,
    category_id: UUID,
    label: str | None = None,
    nature: CategoryNature | None = None,
) -> Category:
    category = category_repository.get_by_id(session, category_id)
    if not category:
        raise ValueError("Category not found")

    if label is not None:
        existing = category_repository.get_by_user_and_label(
            session, category.user_id, label
        )
        if existing and existing.id != category_id:
            raise ValueError("Category with this name already exists")
        category.label = label
    if nature is not None:
        category.nature = nature

    return category_repository.update(session, category)


def delete_category(session: Session, category_id: UUID) -> None:
    category = category_repository.get_by_id(session, category_id)
    if not category:
        raise ValueError("Category not found")

    # Check for subcategories referencing this category
    sub = session.exec(
        select(Subcategory).where(Subcategory.category_id == category_id)
    ).first()
    if sub:
        raise ValueError(
            "Cannot delete category with existing subcategories. "
            "Delete the subcategories first."
        )

    category_repository.delete(session, category)
