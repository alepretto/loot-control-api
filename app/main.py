import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.jobs.scheduler import setup_scheduler
from app.routers import admin, agent, bot, mini, users
from app.routers.finance import categories, market_data, payment_methods, tag_families, tags, transactions

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    scheduler = setup_scheduler()
    scheduler.start()

    if settings.TELEGRAM_BOT_TOKEN:
        try:
            import app.bot.state as bot_state
            from app.bot.setup import create_bot_app
            bot_state.bot_app = create_bot_app()
            await bot_state.bot_app.initialize()
            await bot_state.bot_app.start()

            if settings.WEBHOOK_URL:
                webhook_path = f"/bot/webhook/{settings.TELEGRAM_BOT_TOKEN}"
                await bot_state.bot_app.bot.set_webhook(
                    url=f"{settings.WEBHOOK_URL}{webhook_path}",
                    drop_pending_updates=True,
                )
                logger.info(f"Telegram bot webhook set: {settings.WEBHOOK_URL}{webhook_path}")
            else:
                await bot_state.bot_app.updater.start_polling(drop_pending_updates=True)
                logger.info("Telegram bot started (polling)")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot (API still running): {e}")
            bot_state.bot_app = None

    yield

    import app.bot.state as bot_state
    if bot_state.bot_app is not None:
        if settings.WEBHOOK_URL:
            await bot_state.bot_app.bot.delete_webhook()
        else:
            await bot_state.bot_app.updater.stop()
        await bot_state.bot_app.stop()
        await bot_state.bot_app.shutdown()
        bot_state.bot_app = None

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
app.include_router(mini.router)
app.include_router(bot.router)
app.include_router(tag_families.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(transactions.router)
app.include_router(payment_methods.router)
app.include_router(market_data.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
