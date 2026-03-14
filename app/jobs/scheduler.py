from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.asset_prices import update_asset_prices
from app.jobs.exchange_rates import update_exchange_rates
from app.jobs.reports import daily_reminder, monthly_report, weekly_report

scheduler = AsyncIOScheduler()


def setup_scheduler() -> AsyncIOScheduler:
    # Market data — daily after Brazilian market close
    scheduler.add_job(update_exchange_rates, CronTrigger(hour=21, minute=0), id="exchange_rates")
    scheduler.add_job(update_asset_prices, CronTrigger(hour=21, minute=30), id="asset_prices")

    # Daily reminder — 23:00 UTC (20:00 BRT)
    scheduler.add_job(daily_reminder, CronTrigger(hour=23, minute=0), id="daily_reminder")

    # Weekly report — every Monday at 11:00 UTC (08:00 BRT)
    scheduler.add_job(weekly_report, CronTrigger(day_of_week="mon", hour=11, minute=0), id="weekly_report")

    # Monthly report — 1st of every month at 11:00 UTC (08:00 BRT)
    scheduler.add_job(monthly_report, CronTrigger(day=1, hour=11, minute=0), id="monthly_report")

    return scheduler
