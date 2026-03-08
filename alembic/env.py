import asyncio
from logging.config import fileConfig
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import sqlalchemy
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings
import app.models  # noqa: F401 — registers all models in metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

# asyncpg does not accept Supabase-specific query params (e.g. pgbouncer, sslmode)
_ASYNCPG_UNSUPPORTED_PARAMS = {"pgbouncer", "sslmode", "supa"}


def _clean_url(url: str) -> str:
    """Strip query params unsupported by asyncpg from the connection URL."""
    parsed = urlparse(url)
    if not parsed.query:
        return url
    qs = {k: v for k, v in parse_qs(parsed.query).items() if k not in _ASYNCPG_UNSUPPORTED_PARAMS}
    clean = parsed._replace(query=urlencode(qs, doseq=True))
    return urlunparse(clean)


def _get_db_url() -> str:
    url = settings.DATABASE_URL
    # Ensure we're using the asyncpg driver
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return _clean_url(url)


def run_migrations_offline() -> None:
    context.configure(
        url=_get_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(
        _get_db_url(),
        connect_args={"ssl": "require", "statement_cache_size": 0},
    )
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("CREATE SCHEMA IF NOT EXISTS finance"))
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
