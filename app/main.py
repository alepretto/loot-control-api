from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import create_db_and_tables
from app.models.user import User  # noqa: F401 — ensure model registered
from app.models.account import Account  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.subcategory import Subcategory  # noqa: F401


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

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers import users
    from app.routers import accounts
    from app.routers import categories
    from app.routers import subcategories

    application.include_router(users.router)
    application.include_router(accounts.router)
    application.include_router(categories.router)
    application.include_router(subcategories.router)

    return application


app = create_app()
