from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import create_db_and_tables
from app.models.user import User  # noqa: F401 — ensure model registered
from app.models.account import Account  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.subcategory import Subcategory  # noqa: F401
from app.models.currency import Currency  # noqa: F401
from app.models.credit_card import CreditCard  # noqa: F401
from app.models.credit_card_statement import CreditCardStatement  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.investment_ledger import InvestmentLedger  # noqa: F401


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
    from app.routers import currencies
    from app.routers import credit_cards
    from app.routers import credit_card_statements
    from app.routers import transactions
    from app.routers import investment_ledger

    application.include_router(users.router)
    application.include_router(accounts.router)
    application.include_router(categories.router)
    application.include_router(subcategories.router)
    application.include_router(currencies.router)
    application.include_router(credit_cards.router)
    application.include_router(credit_card_statements.router)
    application.include_router(transactions.router)
    application.include_router(investment_ledger.router)

    return application


app = create_app()
