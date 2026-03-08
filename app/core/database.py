from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

_UNSUPPORTED_PARAMS = {"pgbouncer", "sslmode", "supa"}


def _build_engine_url(url: str) -> str:
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    parsed = urlparse(url)
    if parsed.query:
        qs = {k: v for k, v in parse_qs(parsed.query).items() if k not in _UNSUPPORTED_PARAMS}
        url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
    return url


engine = create_async_engine(
    _build_engine_url(settings.DATABASE_URL),
    connect_args={"statement_cache_size": 0},
    echo=settings.DB_ECHO,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("CREATE SCHEMA IF NOT EXISTS finance"))
        await conn.run_sync(SQLModel.metadata.create_all)
