from __future__ import annotations

import uuid
from calendar import monthrange
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.asset_price import AssetPrice
from app.models.finance.category import Category
from app.models.finance.exchange_rate import ExchangeRate
from app.models.finance.tag import Tag
from app.models.finance.tag_family import FamilyNature, TagFamily
from app.models.finance.transaction import Currencies, Transaction


class SummaryService:
    async def _load_exchange_rates(
        self, session: AsyncSession, dt_from: datetime, dt_to: datetime
    ) -> dict[tuple[str, date], float]:
        try:
            extended_from = (dt_from - timedelta(days=7)).date()
            query = select(ExchangeRate).where(
                ExchangeRate.date >= extended_from,
                ExchangeRate.date <= dt_to.date(),
            )
            results = await session.exec(query)  # type: ignore[call-overload]
            rates: dict[tuple[str, date], float] = {}
            for rate in results.all():
                try:
                    currency_str = rate.currency.value if hasattr(rate.currency, "value") else str(rate.currency)
                    rates[(currency_str, rate.date)] = rate.rate
                except Exception:
                    continue
            return rates
        except Exception:
            return {}

    def _to_brl(
        self,
        value: float,
        currency: Currencies,
        tx_date: datetime,
        rates: dict[tuple[str, date], float],
    ) -> float:
        currency_str = currency.value if hasattr(currency, "value") else str(currency)
        if currency_str == "BRL":
            return value
        check = tx_date.date()
        for days_back in range(8):
            rate = rates.get((currency_str, check - timedelta(days=days_back)))
            if rate:
                return value * rate
        return value

    async def get_monthly_summary(
        self, session: AsyncSession, user_id: uuid.UUID, month: int, year: int
    ) -> dict:
        last_day = monthrange(year, month)[1]
        dt_from = datetime(year, month, 1, tzinfo=UTC)
        dt_to = datetime(year, month, last_day, 23, 59, 59, tzinfo=UTC)

        rates = await self._load_exchange_rates(session, dt_from, dt_to)

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

        totals: dict[str, float] = defaultdict(float)
        family_totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        tag_totals: dict[tuple[str, str, str], float] = defaultdict(float)
        income_type_totals: dict[str, float] = defaultdict(float)

        for tx, tag, cat, family in rows:
            value_brl = self._to_brl(tx.value, tx.currency, tx.date_transaction, rates)
            nature = family.nature.value if family and family.nature else "unknown"
            family_name = family.name if family else "Sem família"

            totals[nature] += value_brl
            family_totals[family_name][nature] += value_brl

            if nature in ("fixed_expense", "variable_expense"):
                tag_totals[(tag.name, cat.name, family_name)] += value_brl

            if nature == "income" and tag.income_type:
                income_type_key = tag.income_type.value if hasattr(tag.income_type, "value") else str(tag.income_type)
                income_type_totals[income_type_key] += value_brl

        total_income = totals.get("income", 0.0)
        total_expense = totals.get("fixed_expense", 0.0) + totals.get("variable_expense", 0.0)
        total_investment = totals.get("investment", 0.0)
        balance = total_income - total_expense - total_investment
        saving_rate = (balance / total_income * 100) if total_income > 0 else 0.0

        by_family = sorted(
            [
                {"family_name": fname, "nature": nature, "total": round(total, 2)}
                for fname, natures in family_totals.items()
                for nature, total in natures.items()
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

        income_by_type = {
            k: round(v, 2) for k, v in income_type_totals.items()
        }

        return {
            "month": month,
            "year": year,
            "total_income": round(total_income, 2),
            "total_fixed_expense": round(totals.get("fixed_expense", 0.0), 2),
            "total_variable_expense": round(totals.get("variable_expense", 0.0), 2),
            "total_investment": round(total_investment, 2),
            "total_expense": round(total_expense, 2),
            "balance": round(balance, 2),
            "saving_rate": round(saving_rate, 2),
            "income_by_type": income_by_type,
            "by_family": by_family,
            "top_tags": top_tags,
            "has_foreign_currency": has_foreign_currency,
        }

    async def get_asset_performance(
        self, session: AsyncSession, user_id: uuid.UUID, date_from: date, date_to: date
    ) -> dict:
        dt_to_end = datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=UTC)
        
        # Otimização: Query única para quantidades por símbolo
        qty_stmt = (
            select(Transaction.symbol, func.coalesce(func.sum(Transaction.quantity), 0.0))
            .where(
                Transaction.user_id == user_id,
                Transaction.symbol.isnot(None),
                Transaction.index.is_(None),
                Transaction.date_transaction <= dt_to_end,
                Transaction.quantity.isnot(None),
            )
            .group_by(Transaction.symbol)
        )
        qty_result = await session.exec(qty_stmt)  # type: ignore[call-overload]
        qty_by_symbol = {row[0]: float(row[1]) for row in qty_result.all() if row[0]}
        symbols = list(qty_by_symbol.keys())
        
        if not symbols:
            return {"period": {"from": str(date_from), "to": str(date_to)}, "assets": []}

        # Otimização: Query única para preços mais próximos de date_from
        price_from_subq = (
            select(
                AssetPrice.symbol,
                AssetPrice.price,
                AssetPrice.date,
                AssetPrice.currency,
                func.row_number().over(
                    partition_by=AssetPrice.symbol,
                    order_by=AssetPrice.date.desc()
                ).label('rn')
            )
            .where(
                AssetPrice.symbol.in_(symbols),
                AssetPrice.date <= date_from
            )
            .subquery()
        )
        price_from_stmt = (
            select(price_from_subq)
            .where(price_from_subq.c.rn == 1)
        )
        price_from_result = await session.exec(price_from_stmt)  # type: ignore[call-overload]
        price_from_map = {
            row[0]: {"price": float(row[1]), "date": row[2], "currency": row[3]}
            for row in price_from_result.all()
        }
        
        # Otimização: Query única para preços mais próximos de date_to
        price_to_subq = (
            select(
                AssetPrice.symbol,
                AssetPrice.price,
                AssetPrice.date,
                AssetPrice.currency,
                func.row_number().over(
                    partition_by=AssetPrice.symbol,
                    order_by=AssetPrice.date.desc()
                ).label('rn')
            )
            .where(
                AssetPrice.symbol.in_(symbols),
                AssetPrice.date <= date_to
            )
            .subquery()
        )
        price_to_stmt = (
            select(price_to_subq)
            .where(price_to_subq.c.rn == 1)
        )
        price_to_result = await session.exec(price_to_stmt)  # type: ignore[call-overload]
        price_to_map = {
            row[0]: {"price": float(row[1]), "date": row[2], "currency": row[3]}
            for row in price_to_result.all()
        }
        
        # Montar resultado
        performance = []
        for symbol in symbols:
            total_qty = qty_by_symbol.get(symbol, 0.0)
            price_from = price_from_map.get(symbol)
            price_to = price_to_map.get(symbol)
            
            if price_from and price_to and price_from["price"] > 0:
                change_pct = (price_to["price"] - price_from["price"]) / price_from["price"] * 100
                performance.append({
                    "symbol": symbol,
                    "price_start": price_from["price"],
                    "price_end": price_to["price"],
                    "date_start": str(price_from["date"]),
                    "date_end": str(price_to["date"]),
                    "change_pct": round(change_pct, 2),
                    "quantity": float(total_qty),
                    "value_end": round(float(total_qty) * price_to["price"], 2) if total_qty else None,
                    "currency": price_to["currency"].value if hasattr(price_to["currency"], "value") else str(price_to["currency"]),
                })

        performance.sort(key=lambda x: x["change_pct"], reverse=True)
        return {"period": {"from": str(date_from), "to": str(date_to)}, "assets": performance}
