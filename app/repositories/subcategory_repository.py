from uuid import UUID

from sqlmodel import Session, select

from app.models.subcategory import Subcategory


def get_by_id(session: Session, subcategory_id: UUID) -> Subcategory | None:
    return session.get(Subcategory, subcategory_id)


def get_all_by_user(session: Session, user_id: UUID) -> list[Subcategory]:
    statement = select(Subcategory).where(Subcategory.user_id == user_id)
    return list(session.exec(statement).all())


def create(session: Session, subcategory: Subcategory) -> Subcategory:
    session.add(subcategory)
    session.commit()
    session.refresh(subcategory)
    return subcategory


def update(session: Session, subcategory: Subcategory) -> Subcategory:
    session.add(subcategory)
    session.commit()
    session.refresh(subcategory)
    return subcategory


def delete(session: Session, subcategory: Subcategory) -> None:
    session.delete(subcategory)
    session.commit()
