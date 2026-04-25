import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.account import Account  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.subcategory import Subcategory  # noqa: F401
from app.models.currency import Currency  # noqa: F401
from app.models.credit_card import CreditCard  # noqa: F401
from app.models.credit_card_statement import CreditCardStatement  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.investment_ledger import InvestmentLedger  # noqa: F401


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app = create_app()

    from app.core.database import get_session

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="admin_user")
def admin_user_fixture(session: Session) -> User:
    user = User(
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
        password=hash_password("admin123"),
        role="admin",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="normal_user")
def normal_user_fixture(session: Session) -> User:
    user = User(
        first_name="Normal",
        last_name="User",
        email="user@test.com",
        password=hash_password("user123"),
        role="user",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="admin_token")
def admin_token_fixture(admin_user: User) -> str:
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture(name="user_token")
def user_token_fixture(normal_user: User) -> str:
    return create_access_token(data={"sub": str(normal_user.id)})


@pytest.fixture(name="admin_headers")
def admin_headers_fixture(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(name="user_headers")
def user_headers_fixture(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}
