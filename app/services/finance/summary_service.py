import uuid
from calendar import monthrange
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.asset_price import AssetPrice
from app.models.finance.category import Category
from app.models.finance.exchange_rate import ExchangeRate
from app.models.finance.tag import CategoryType, Tag
from app.models.finance.tag_family import TagFamily
from app.models.finance.transaction import Currencies, Transaction


class SummaryService:
    async def _load_exchange_rates(
        self, session: AsyncSession, dt_from: datetime, dt_to: datetime
    ) -> dict[tuple[str, date], float]:
        """Returns {(currency, date): rate_in_brl} for the period + 7 days before."""
        extended_from = (dt_from - timedelta(days=7)).date()
        query = select(ExchangeRate).where(
            ExchangeRate.date >= extended_from,
            ExchangeRate.date <= dt_to.date(),
        )
        result = await session.exec(query)  # type: ignore[call-overload]
        rates: dict[tuple[str, date], float] = {}
        for rate in result.all():
            currency_str = rate.currency.value if hasattr(rate.currency, "value") else str(rate.currency)
            rates[(currency_str, rate.date)] = rate.rate
        return rates

    def _to_brl(
        self,
        value: float,
        currency: Currencies,
        tx_date: datetime,
        rates: dict[tuple[str, date], float],
    ) -> float:
        """Convert a value to BRL using the closest available exchange rate."""
        currency_str = currency.value if hasattr(currency, "value") else str(currency)
        if currency_str == "BRL":
            return value
        check = tx_date.date()
        for days_back in range(8):
            rate = rates.get((currency_str, check - timedelta(days=days_back)))
            if rate:
                return value * rate
        return value  # fallback: no rate found, use raw value

    async def get_monthly_summary(
        self, session: AsyncSession, user_id: uuid.UUID, month: int, year: int
    ) -> dict:
        last_day = monthrange(year, month)[1]
        dt_from = datetime(year, month, 1, tzinfo=UTC)
        dt_to = datetime(year, month, last_day, 23, 59, 59, tzinfo=UTC)

        # Load exchange rates for the period
        rates = await self._load_exchange_rates(session, dt_from, dt_to)

        # Fetch all transactions with tag + category + family
        query = (
            select(Transaction, Tag, Category, TagFamily)
            .join(Tag, Transaction.tag_id == Tag.id)
            .join(Category, Tag.category_id == Category.id)
            .outerjoin(TagFamily, Category.family_id == TagFamily.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.date_transaction >= dt_from,
                Transaction.date_transaction <= dt_to,
            )
        )
        result = await session.exec(query)  # type: ignore[call-overload]
        rows = result.all()

        total_income = 0.0
        total_outcome = 0.0

        # For breakdowns: {family_name: {type: total}}
        family_totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        # For top tags: {(tag_name, cat_name, family_name): total}
        tag_totals: dict[tuple[str, str, str], float] = defaultdict(float)

        for tx, tag, cat, family in rows:
            value_brl = self._to_brl(tx.value, tx.currency, tx.date_transaction, rates)
            type_str = tag.type.value if hasattr(tag.type, "value") else str(tag.type)
            family_name = family.name if family else "Sem família"
            cat_name = cat.name

            if tag.type == CategoryType.income:
                total_income += value_brl
            else:
                total_outcome += value_brl

            family_totals[family_name][type_str] += value_brl

            if tag.type == CategoryType.outcome:
                tag_totals[(tag.name, cat_name, family_name)] += value_brl

        balance = total_income - total_outcome
        saving_rate = (balance / total_income * 100) if total_income > 0 else 0.0

        by_family = sorted(
            [
                {"family_name": fname, "total": round(total, 2), "type": ttype}
                for fname, types in family_totals.items()
                for ttype, total in types.items()
            ],
            key=lambda x: x["total"],
            reverse=True,
        )

        top_tags = sorted(
            [
                {
                    "tag_name": tag_name,
                    "category_name": cat_name,
                    "family_name": fam_name,
                    "total": round(total, 2),
                }
                for (tag_name, cat_name, fam_name), total in tag_totals.items()
            ],
            key=lambda x: x["total"],
            reverse=True,
        )[:10]

        has_foreign_currency = any(
            (tx.currency.value if hasattr(tx.currency, "value") else str(tx.currency)) != "BRL"
            for tx, *_ in rows
        )

        return {
            "month": month,
            "year": year,
            "total_income": round(total_income, 2),
            "total_outcome": round(total_outcome, 2),
            "balance": round(balance, 2),
            "saving_rate": round(saving_rate, 2),
            "by_family": by_family,
            "top_tags": top_tags,
            "has_foreign_currency": has_foreign_currency,
        }

    async def get_asset_performance(
        self, session: AsyncSession, user_id: uuid.UUID, date_from: date, date_to: date
    ) -> dict:
        symbols_query = (
            select(Transaction.symbol)
            .where(
                Transaction.user_id == user_id,
                Transaction.symbol.isnot(None),
                Transaction.index.is_(None),  # renda fixa tem index — sem preço de mercado
            )
            .distinct()
        )
        symbols_result = await session.exec(symbols_query)  # type: ignore[call-overload]
        symbols = [s for s in symbols_result.all() if s]

        if not symbols:
            return {"period": {"from": str(date_from), "to": str(date_to)}, "assets": []}

        performance = []
        for symbol in symbols:
            qty_query = select(Transaction.quantity).where(
                Transaction.user_id == user_id,
                Transaction.symbol == symbol,
                Transaction.date_transaction <= datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=UTC),
                Transaction.quantity.isnot(None),
            )
            qty_result = await session.exec(qty_query)  # type: ignore[call-overload]
            quantities = qty_result.all()
            total_qty = sum(q for q in quantities if q) or 0.0

            price_from_q = (
                select(AssetPrice)
                .where(AssetPrice.symbol == symbol, AssetPrice.date <= date_from)
                .order_by(AssetPrice.date.desc())
                .limit(1)
            )
            price_from_r = await session.exec(price_from_q)  # type: ignore[call-overload]
            price_from = price_from_r.first()

            price_to_q = (
                select(AssetPrice)
                .where(AssetPrice.symbol == symbol, AssetPrice.date <= date_to)
                .order_by(AssetPrice.date.desc())
                .limit(1)
            )
            price_to_r = await session.exec(price_to_q)  # type: ignore[call-overload]
            price_to = price_to_r.first()

            if price_from and price_to and price_from.price > 0:
                change_pct = (price_to.price - price_from.price) / price_from.price * 100
                performance.append({
                    "symbol": symbol,
                    "price_start": price_from.price,
                    "price_end": price_to.price,
                    "date_start": str(price_from.date),
                    "date_end": str(price_to.date),
                    "change_pct": round(change_pct, 2),
                    "quantity": float(total_qty),
                    "value_end": round(float(total_qty) * price_to.price, 2) if total_qty else None,
                    "currency": price_to.currency.value if hasattr(price_to.currency, "value") else str(price_to.currency),
                })

        performance.sort(key=lambda x: x["change_pct"], reverse=True)
        return {"period": {"from": str(date_from), "to": str(date_to)}, "assets": performance}
