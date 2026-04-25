from uuid import UUID

from sqlmodel import Session, select

from app.models.category import Category


def get_by_id(session: Session, category_id: UUID) -> Category | None:
    return session.get(Category, category_id)


def get_all_by_user(session: Session, user_id: UUID) -> list[Category]:
    statement = select(Category).where(Category.user_id == user_id)
    return list(session.exec(statement).all())


def get_by_user_and_label(session: Session, user_id: UUID, label: str) -> Category | None:
    statement = select(Category).where(Category.user_id == user_id, Category.label == label)
    return session.exec(statement).first()


def create(session: Session, category: Category) -> Category:
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def update(session: Session, category: Category) -> Category:
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete(session: Session, category: Category) -> None:
    session.delete(category)
    session.commit()
