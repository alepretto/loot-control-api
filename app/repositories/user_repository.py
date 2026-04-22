from uuid import UUID

from sqlmodel import Session, select

from app.models.user import User


def get_by_id(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)


def get_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_all(session: Session) -> list[User]:
    return list(session.exec(select(User)).all())


def create(session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user