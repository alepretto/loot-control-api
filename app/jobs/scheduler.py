from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.exchange_rates import update_exchange_rates
from app.jobs.asset_prices import update_asset_prices

scheduler = AsyncIOScheduler()


def setup_scheduler() -> AsyncIOScheduler:
    # Daily at 21:00 UTC — after Brazilian market close
    scheduler.add_job(update_exchange_rates, CronTrigger(hour=21, minute=0), id="exchange_rates")
    scheduler.add_job(update_asset_prices, CronTrigger(hour=21, minute=30), id="asset_prices")
    return scheduler
