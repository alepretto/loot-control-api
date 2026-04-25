from collections import defaultdict
from datetime import date
from uuid import UUID

from sqlmodel import Session

from app.models.investment_ledger import InvestmentLedger
from app.repositories import (
    asset_price_repository,
    exchange_rate_repository,
    investment_ledger_repository,
)
from app.services import asset_price_service, exchange_rate_service


def create_investment(
    session: Session,
    user_id: UUID,
    transaction_id: UUID,
    symbol: str,
    quantity: float,
    index: str | None = None,
    index_rate: float | None = None,
    currency: str = "BRL",
    purchase_exchange_rate: float | None = None,
) -> InvestmentLedger:
    ledger = InvestmentLedger(
        user_id=user_id,
        transaction_id=transaction_id,
        symbol=symbol,
        quantity=quantity,
        index=index,
        index_rate=index_rate,
        currency=currency,
        purchase_exchange_rate=purchase_exchange_rate,
    )
    return investment_ledger_repository.create(session, ledger)


def list_investments(session: Session, user_id: UUID) -> list[InvestmentLedger]:
    return investment_ledger_repository.get_all_by_user(session, user_id)


def get_investment_by_id(session: Session, ledger_id: UUID) -> InvestmentLedger:
    ledger = investment_ledger_repository.get_by_id(session, ledger_id)
    if not ledger:
        raise ValueError("Investment not found")
    return ledger


def update_investment(
    session: Session,
    ledger_id: UUID,
    transaction_id: UUID | None = None,
    symbol: str | None = None,
    quantity: float | None = None,
    index: str | None = None,
    index_rate: float | None = None,
    currency: str | None = None,
    purchase_exchange_rate: float | None = None,
) -> InvestmentLedger:
    ledger = investment_ledger_repository.get_by_id(session, ledger_id)
    if not ledger:
        raise ValueError("Investment not found")

    if transaction_id is not None:
        ledger.transaction_id = transaction_id
    if symbol is not None:
        ledger.symbol = symbol
    if quantity is not None:
        ledger.quantity = quantity
    if index is not None:
        ledger.index = index
    if index_rate is not None:
        ledger.index_rate = index_rate
    if currency is not None:
        ledger.currency = currency
    if purchase_exchange_rate is not None:
        ledger.purchase_exchange_rate = purchase_exchange_rate

    return investment_ledger_repository.update(session, ledger)


def get_investments_with_relations(session: Session, user_id: UUID) -> list[dict]:
    """Returns investments with joined transaction/currency/category data for portfolio calc."""
    return investment_ledger_repository.get_by_user_with_relations(session, user_id)


def delete_investment(session: Session, ledger_id: UUID) -> None:
    ledger = investment_ledger_repository.get_by_id(session, ledger_id)
    if not ledger:
        raise ValueError("Investment not found")
    investment_ledger_repository.delete(session, ledger)


def _parse_date(raw_date) -> date:
    """Safely convert a raw date value from DB query to a date object."""
    if isinstance(raw_date, date):
        return raw_date
    if isinstance(raw_date, str):
        return date.fromisoformat(raw_date[:10])
    raise TypeError(f"Cannot parse date from {type(raw_date)}: {raw_date}")


def _calc_invested_brl(
    currency: str,
    amount: float,
    purchase_exchange_rate: float | None,
) -> float:
    """Calculate the invested amount in BRL for a single investment row."""
    if currency == "BRL" or not purchase_exchange_rate:
        return amount
    return amount * purchase_exchange_rate


def get_portfolio_summary(session: Session, user_id: UUID) -> dict:
    """Returns aggregated portfolio P&L grouped by category.

    Response structure:
    {
        "total_invested": float,
        "total_current_value": float,
        "total_return": float,
        "total_return_pct": float,
        "by_category": [...]
    }
    """
    rows = investment_ledger_repository.get_by_user_with_relations(session, user_id)
    if not rows:
        return {
            "total_invested": 0.0,
            "total_current_value": 0.0,
            "total_return": 0.0,
            "total_return_pct": 0.0,
            "by_category": [],
        }

    # --- 1. Fetch latest prices for all unique symbols ---
    symbols = {r["symbol"] for r in rows}
    latest_prices: dict[str, float | None] = {}
    for sym in symbols:
        price_obj = asset_price_service.get_latest_by_symbol(session, sym)
        latest_prices[sym] = price_obj.price if price_obj else None

    # --- 2. Fetch latest exchange rates for all non-BRL currencies ---
    non_brl_currencies = {r["currency"] for r in rows if r["currency"] != "BRL"}
    exchange_rates: dict[str, float | None] = {}
    for curr in non_brl_currencies:
        try:
            rate_obj = exchange_rate_service.get_latest_rate(session, curr, "BRL")
            exchange_rates[curr] = rate_obj.rate
        except ValueError:
            exchange_rates[curr] = None

    # --- 3. Group by category → symbol, aggregate quantities & invested ---
    # categories[cat_label][symbol] = {"quantity": float, "total_invested": float, "currency": str}
    categories: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"quantity": 0.0, "total_invested": 0.0, "currency": "BRL"}))  # type: ignore

    for row in rows:
        cat_label: str = row["category_label"]
        sym: str = row["symbol"]
        qty: float = row["quantity"]
        currency: str = row["currency"]
        purchase_exchange_rate: float | None = row.get("purchase_exchange_rate")
        amount: float = float(row["amount"])

        invested_brl = _calc_invested_brl(currency, amount, purchase_exchange_rate)

        agg = categories[cat_label][sym]
        agg["quantity"] += qty
        agg["total_invested"] += invested_brl
        if agg["currency"] == "BRL" and currency != "BRL":
            agg["currency"] = currency

    # --- 4. Build response ---
    portfolio_total_invested = 0.0
    portfolio_total_current_value = 0.0
    by_category: list[dict] = []

    for cat_label, sym_aggs in categories.items():
        cat_total_invested = 0.0
        cat_total_current_value = 0.0
        assets: list[dict] = []

        for sym, agg in sym_aggs.items():
            total_invested = agg["total_invested"]
            quantity = agg["quantity"]
            currency = agg["currency"]

            current_price = latest_prices.get(sym)

            rate: float | None = 1.0
            if currency != "BRL":
                rate = exchange_rates.get(currency)

            if current_price is not None and rate is not None:
                current_value = quantity * current_price * rate
            else:
                current_value = 0.0

            sym_return = current_value - total_invested
            sym_return_pct = (
                (sym_return / total_invested * 100) if total_invested else 0.0
            )

            cat_total_invested += total_invested
            cat_total_current_value += current_value

            assets.append({
                "symbol": sym,
                "quantity": quantity,
                "total_invested": round(total_invested, 2),
                "current_price": current_price,
                "current_value": round(current_value, 2),
                "return_pct": round(sym_return_pct, 2),
                "weight_in_category": 0.0,
            })

        # Fill weight_in_category for each asset
        for asset in assets:
            if cat_total_current_value:
                asset["weight_in_category"] = round(
                    asset["current_value"] / cat_total_current_value * 100, 2
                )

        cat_return = cat_total_current_value - cat_total_invested
        cat_return_pct = (
            (cat_return / cat_total_invested * 100) if cat_total_invested else 0.0
        )

        portfolio_total_invested += cat_total_invested
        portfolio_total_current_value += cat_total_current_value

        by_category.append({
            "category": cat_label,
            "total_invested": round(cat_total_invested, 2),
            "total_current_value": round(cat_total_current_value, 2),
            "total_return": round(cat_return, 2),
            "total_return_pct": round(cat_return_pct, 2),
            "weight_pct": 0.0,
            "assets": assets,
        })

    # Fill weight_pct for each category
    for cat in by_category:
        if portfolio_total_current_value:
            cat["weight_pct"] = round(
                cat["total_current_value"] / portfolio_total_current_value * 100, 2
            )

    total_return = portfolio_total_current_value - portfolio_total_invested
    total_return_pct = (
        (total_return / portfolio_total_invested * 100) if portfolio_total_invested else 0.0
    )

    return {
        "total_invested": round(portfolio_total_invested, 2),
        "total_current_value": round(portfolio_total_current_value, 2),
        "total_return": round(total_return, 2),
        "total_return_pct": round(total_return_pct, 2),
        "by_category": by_category,
    }


def get_portfolio_timeline(
    session: Session,
    user_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Returns portfolio value over time, one entry per transaction date.

    Each entry: {"date": str, "cumulative_invested": float, "market_value": float}
    """
    rows = investment_ledger_repository.get_by_user_with_relations(session, user_id)
    if not rows:
        return []

    # --- 1. Parse & filter by date range ---
    for row in rows:
        row["_parsed_date"] = _parse_date(row["date_transaction"])

    if start_date:
        rows = [r for r in rows if r["_parsed_date"] >= start_date]
    if end_date:
        rows = [r for r in rows if r["_parsed_date"] <= end_date]

    if not rows:
        return []

    rows.sort(key=lambda r: r["_parsed_date"])

    # --- 2. Pre-fetch all prices & rates ---
    symbols = {r["symbol"] for r in rows}
    all_prices: dict[str, list] = {}
    for sym in symbols:
        all_prices[sym] = asset_price_repository.get_all(session, symbol=sym)

    non_brl = {r["currency"] for r in rows if r["currency"] != "BRL"}
    all_rates: dict[str, list] = {}
    for curr in non_brl:
        all_rates[curr] = exchange_rate_repository.get_all(
            session, from_currency=curr, to_currency="BRL"
        )

    # Map each symbol to its currency (from the first occurrence)
    symbol_currency: dict[str, str] = {}
    for r in rows:
        sym = r["symbol"]
        if sym not in symbol_currency:
            symbol_currency[sym] = r["currency"]

    # --- 3. Group rows by transaction date ---
    by_date: dict[date, list] = defaultdict(list)
    for r in rows:
        by_date[r["_parsed_date"]].append(r)

    # --- 4. Walk sorted dates, accumulate ---
    running_qty: dict[str, float] = defaultdict(float)
    cumulative_invested = 0.0
    timeline: list[dict] = []

    for tx_date in sorted(by_date.keys()):
        date_rows = by_date[tx_date]

        for row in date_rows:
            sym = row["symbol"]
            qty = row["quantity"]
            currency = row["currency"]
            purchase_exchange_rate = row.get("purchase_exchange_rate")
            amount = float(row["amount"])

            running_qty[sym] += qty
            cumulative_invested += _calc_invested_brl(
                currency, amount, purchase_exchange_rate
            )

        # Calculate market value using nearest available prices
        market_value = 0.0
        for sym, qty in running_qty.items():
            if qty == 0:
                continue

            # Nearest price on or before this date
            current_price: float | None = None
            for p in all_prices.get(sym, []):
                if p.price_date <= tx_date:
                    current_price = p.price
                    break

            if current_price is None:
                continue

            # Exchange rate if not BRL
            rate = 1.0
            curr_currency = symbol_currency.get(sym, "BRL")
            if curr_currency != "BRL":
                nearest_rate: float | None = None
                for r in all_rates.get(curr_currency, []):
                    if r.rate_date <= tx_date:
                        nearest_rate = r.rate
                        break
                if nearest_rate is None:
                    continue
                rate = nearest_rate

            market_value += qty * current_price * rate

        timeline.append({
            "date": tx_date.isoformat(),
            "cumulative_invested": round(cumulative_invested, 2),
            "market_value": round(market_value, 2),
        })

    return timeline
