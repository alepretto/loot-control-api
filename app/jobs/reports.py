import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.bot.telegram import send_message_to_user
from app.core.config import settings
from app.core.database import engine
from app.models.finance.tag import CategoryType
from app.models.finance.transaction import Currencies, Transaction
from app.models.user import User
from app.services.finance.summary_service import SummaryService

logger = logging.getLogger(__name__)
summary_service = SummaryService()

MONTH_NAMES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def _brl(value: float) -> str:
    """Format float as Brazilian currency string."""
    formatted = f"{value:,.2f}"
    parts = formatted.split(".")
    integer_part = parts[0].replace(",", ".")
    return f"R$ {integer_part},{parts[1]}"


async def _get_users_with_telegram(session: AsyncSession) -> list[uuid.UUID]:
    """Return list of user IDs that have a telegram_id linked."""
    result = await session.exec(
        select(User.id).where(User.telegram_id.is_not(None))  # type: ignore[union-attr]
    )
    return list(result.all())


async def daily_reminder() -> None:
    """Send a reminder to each user who has no transactions today."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    today = datetime.now(UTC).date()
    dt_from = datetime(today.year, today.month, today.day, tzinfo=UTC)
    dt_to = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=UTC)

    try:
        async with AsyncSession(engine) as session:
            user_ids = await _get_users_with_telegram(session)

            for user_id in user_ids:
                query = (
                    select(Transaction.id)
                    .where(
                        Transaction.user_id == user_id,
                        Transaction.date_transaction >= dt_from,
                        Transaction.date_transaction <= dt_to,
                    )
                    .limit(1)
                )
                result = await session.exec(query)  # type: ignore[call-overload]
                has_transactions = result.first() is not None

                if not has_transactions:
                    await send_message_to_user(
                        session,
                        user_id,
                        f"📋 *Lembrete diário*\n\nVocê não registrou nenhuma transação hoje ({today.strftime('%d/%m/%Y')}). "
                        "Não esqueça de anotar seus gastos!",
                    )
    except Exception as e:
        logger.error(f"daily_reminder error: {e}", exc_info=True)


async def weekly_report() -> None:
    """Send a weekly summary to each linked user."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    today = datetime.now(UTC).date()
    week_end = today - timedelta(days=1)
    week_start = week_end - timedelta(days=6)

    dt_from = datetime(week_start.year, week_start.month, week_start.day, tzinfo=UTC)
    dt_to = datetime(week_end.year, week_end.month, week_end.day, 23, 59, 59, tzinfo=UTC)

    try:
        async with AsyncSession(engine) as session:
            from app.models.finance.tag import Tag

            user_ids = await _get_users_with_telegram(session)

            for user_id in user_ids:
                query = (
                    select(Tag.type, func.sum(Transaction.value).label("total"))
                    .join(Tag, Transaction.tag_id == Tag.id)
                    .where(
                        Transaction.user_id == user_id,
                        Transaction.currency == Currencies.BRL,
                        Transaction.date_transaction >= dt_from,
                        Transaction.date_transaction <= dt_to,
                    )
                    .group_by(Tag.type)
                )
                result = await session.exec(query)  # type: ignore[call-overload]
                rows = result.all()

                income = sum(float(r.total) for r in rows if r[0] == CategoryType.income)
                outcome = sum(float(r.total) for r in rows if r[0] == CategoryType.outcome)
                balance = income - outcome
                balance_icon = "💰" if balance >= 0 else "⚠️"

                text = (
                    f"📊 *Relatório Semanal*\n"
                    f"{week_start.strftime('%d/%m')} a {week_end.strftime('%d/%m/%Y')}\n\n"
                    f"💚 Entradas: {_brl(income)}\n"
                    f"🔴 Saídas: {_brl(outcome)}\n"
                    f"{balance_icon} Saldo: {_brl(balance)}"
                )
                await send_message_to_user(session, user_id, text)
    except Exception as e:
        logger.error(f"weekly_report error: {e}", exc_info=True)


async def monthly_report() -> None:
    """Send a monthly summary to each linked user."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    today = datetime.now(UTC)
    month = today.month - 1 if today.month > 1 else 12
    year = today.year if today.month > 1 else today.year - 1

    try:
        async with AsyncSession(engine) as session:
            user_ids = await _get_users_with_telegram(session)

            for user_id in user_ids:
                data = await summary_service.get_monthly_summary(session, user_id, month, year)

                balance_icon = "💰" if data["balance"] >= 0 else "⚠️"
                top_lines = "\n".join(
                    f"  • {t['tag_name']}: {_brl(t['total'])}"
                    for t in data["top_tags"][:5]
                )

                text = (
                    f"📅 *Relatório de {MONTH_NAMES[month - 1]} {year}*\n\n"
                    f"💚 Entradas: {_brl(data['total_income'])}\n"
                    f"🔴 Saídas: {_brl(data['total_outcome'])}\n"
                    f"{balance_icon} Saldo: {_brl(data['balance'])}\n"
                    f"📈 Saving Rate: {data['saving_rate']:.1f}%\n"
                )
                if top_lines:
                    text += f"\n*Top gastos:*\n{top_lines}"

                await send_message_to_user(session, user_id, text)
    except Exception as e:
        logger.error(f"monthly_report error: {e}", exc_info=True)
