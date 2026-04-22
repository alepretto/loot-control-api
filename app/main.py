from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import create_db_and_tables
from app.models.user import User  # noqa: F401 — ensure model registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Loot Control API",
        version="2.0.0",
        description="Sistema de gestão financeira pessoal",
        lifespan=lifespan,
    )

    from app.routers import users

    application.include_router(users.router)

    return application


app = create_app()