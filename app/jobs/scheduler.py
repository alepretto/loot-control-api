from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.asset_prices import update_asset_prices
from app.jobs.exchange_rates import update_exchange_rates
from app.jobs.reports import daily_reminder, monthly_report, weekly_report

scheduler = AsyncIOScheduler()


def setup_scheduler() -> AsyncIOScheduler:
    BRT = "America/Sao_Paulo"

    # Market data — 3x/dia no horário de Brasília
    scheduler.add_job(update_exchange_rates, CronTrigger(hour="9,15,18", minute=0, timezone=BRT), id="exchange_rates")
    scheduler.add_job(update_asset_prices, CronTrigger(hour="9,15,18", minute=30, timezone=BRT), id="asset_prices")

    # Daily reminder — 20:00 BRT
    scheduler.add_job(daily_reminder, CronTrigger(hour=20, minute=0, timezone=BRT), id="daily_reminder")

    # Weekly report — toda segunda às 08:00 BRT
    scheduler.add_job(weekly_report, CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=BRT), id="weekly_report")

    # Monthly report — dia 1 de cada mês às 08:00 BRT
    scheduler.add_job(monthly_report, CronTrigger(day=1, hour=8, minute=0, timezone=BRT), id="monthly_report")

    return scheduler
