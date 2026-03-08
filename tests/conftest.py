import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import sqlalchemy
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from testcontainers.postgres import PostgresContainer

import app.models  # noqa: F401 — registers all models in metadata
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.main import app
from app.models.user import User

TEST_USER_ID = str(uuid.uuid4())


@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def db_url(postgres):
    url = postgres.get_connection_url()
    # testcontainers returns psycopg2 URL; swap driver for asyncpg
    return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


@pytest_asyncio.fixture(scope="session")
async def engine(db_url):
    _engine = create_async_engine(db_url, echo=False)
    async with _engine.begin() as conn:
        await conn.execute(sqlalchemy.text("CREATE SCHEMA IF NOT EXISTS finance"))
        await conn.run_sync(SQLModel.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as _session:
        yield _session
        await _session.rollback()


@pytest_asyncio.fixture
async def test_user(session: AsyncSession) -> User:
    user = User(
        id=uuid.UUID(TEST_USER_ID),
        email=f"test-{uuid.uuid4()}@lootcontrol.com",
        username=f"testuser-{uuid.uuid4().hex[:6]}",
        first_name="Test",
        last_name="User",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def client(session: AsyncSession, test_user: User) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_current_user_id] = lambda: str(test_user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
