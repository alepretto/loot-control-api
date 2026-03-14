import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import sqlalchemy
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from testcontainers.postgres import PostgresContainer

import app.models  # noqa: F401 — registers all models in metadata
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.main import app
from app.models.user import User


# ---------------------------------------------------------------------------
# Database container — one per test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def db_url(postgres):
    url = postgres.get_connection_url()
    return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def engine(db_url):
    """
    Sync fixture so it lives outside any async event loop.
    Creates the schema once, then disposes the pool so each test's
    function-scoped loop creates its own fresh connections.
    """
    # NullPool: no connection reuse across event loops (each test has its own loop)
    _engine = create_async_engine(db_url, echo=False, poolclass=NullPool)

    async def _setup():
        async with _engine.begin() as conn:
            await conn.execute(sqlalchemy.text("CREATE SCHEMA IF NOT EXISTS finance"))
            await conn.execute(sqlalchemy.text("CREATE SCHEMA IF NOT EXISTS agent"))
            await conn.run_sync(SQLModel.metadata.create_all)
        # Dispose pool so no loop-tied connections linger for the tests
        await _engine.dispose()

    asyncio.run(_setup())
    yield _engine
    asyncio.run(_engine.dispose())


# ---------------------------------------------------------------------------
# Per-test session — fresh async session in the test's own event loop
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as _session:
        yield _session
        await _session.rollback()


# ---------------------------------------------------------------------------
# Test user — unique per test, no cross-test conflicts
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_user(session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4()}@lootcontrol.com",
        username=f"testuser-{uuid.uuid4().hex[:8]}",
        first_name="Test",
        last_name="User",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# HTTP client with dependency overrides
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(session: AsyncSession, test_user: User) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_current_user_id] = lambda: str(test_user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
