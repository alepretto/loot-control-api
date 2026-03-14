import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.jobs.scheduler import setup_scheduler
from app.routers import admin, agent, users
from app.routers.finance import categories, market_data, tag_families, tags, transactions

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    scheduler = setup_scheduler()
    scheduler.start()

    bot_app = None
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            from app.bot.setup import create_bot_app
            bot_app = create_bot_app()
            await bot_app.initialize()
            await bot_app.start()
            await bot_app.updater.start_polling()
            logger.info("Telegram bot started")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot (API still running): {e}")
            bot_app = None

    yield

    if bot_app is not None:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()

    scheduler.shutdown()


app = FastAPI(title="Loot Control API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(users.router)
app.include_router(admin.router)
app.include_router(agent.router)
app.include_router(tag_families.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(transactions.router)
app.include_router(market_data.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
