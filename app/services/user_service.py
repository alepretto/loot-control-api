from uuid import UUID

from sqlmodel import Session

from app.core.security import hash_password, create_access_token, verify_password
from app.models.user import User
from app.repositories import user_repository


def signup(session: Session, first_name: str, last_name: str, email: str, password: str) -> User:
    existing = user_repository.get_by_email(session, email)
    if existing:
        raise ValueError("Email already registered")

    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hash_password(password),
    )
    return user_repository.create(session, user)


def login(session: Session, email: str, password: str) -> str:
    user = user_repository.get_by_email(session, email)
    if not user or not verify_password(password, user.password):
        raise ValueError("Invalid credentials")
    if not user.is_active:
        raise ValueError("Inactive user")

    return create_access_token(data={"sub": str(user.id)})


def get_me(session: Session, user: User) -> User:
    return user


def get_user_by_id(session: Session, user_id: UUID) -> User:
    user = user_repository.get_by_id(session, user_id)
    if not user:
        raise ValueError("User not found")
    return user


def list_users(session: Session) -> list[User]:
    return user_repository.get_all(session)


def update_preferences(
    session: Session,
    user: User,
    display_currency_id: UUID | None,
) -> User:
    user.display_currency_id = display_currency_id
    session.add(user)
    session.commit()
    session.refresh(user)
    return user