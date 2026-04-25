"""
update_prices.py — Fetch current market prices from Yahoo Finance and store in DB.

Usage:
    python scripts/update_prices.py --db-url "sqlite:///data.db"
    python scripts/update_prices.py --db-url "sqlite:///data.db" --tickers "PETR4.SA,AAPL,BRL=X"
"""

import argparse
import uuid
from datetime import date, datetime

try:
    import yfinance as yf
except ImportError:
    print("Error: yfinance is not installed. Run: uv add yfinance")
    raise SystemExit(1)

from sqlalchemy import create_engine, text


DEFAULT_TICKERS = [
    "PETR4.SA", "VALE3.SA", "ITSA4.SA", "ABEV3.SA",
    "WEGE3.SA", "BBAS3.SA", "B3SA3.SA", "RENT3.SA",
    "LREN3.SA", "MGLU3.SA",
    "AAPL", "MSFT", "GOOGL", "AMZN",
    "BTC-USD", "ETH-USD",
    "BRL=X",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Update asset prices and exchange rates")
    parser.add_argument(
        "--db-url",
        required=True,
        help="SQLite database URL (e.g., sqlite:///path/to/db.sqlite)",
    )
    parser.add_argument(
        "--tickers",
        default=",".join(DEFAULT_TICKERS),
        help="Comma-separated ticker symbols (default: Brazilian stocks + US stocks + crypto + FX)",
    )
    return parser.parse_args()


def store_asset_price(engine, symbol: str, price: float, currency: str):
    """Insert or update (upsert) asset price for today."""
    today = date.today().isoformat()
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM asset_prices WHERE symbol = :symbol AND price_date = :date"),
            {"symbol": symbol, "date": today},
        ).fetchone()

        if existing:
            conn.execute(
                text("UPDATE asset_prices SET price = :price, currency = :currency WHERE id = :id"),
                {"price": price, "currency": currency, "id": existing[0]},
            )
            print(f"  Updated {symbol}: {price} {currency}")
        else:
            conn.execute(
                text(
                    "INSERT INTO asset_prices (id, symbol, price_date, price, currency, created_at) "
                    "VALUES (:id, :symbol, :date, :price, :currency, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "symbol": symbol,
                    "date": today,
                    "price": price,
                    "currency": currency,
                    "now": datetime.utcnow().isoformat(),
                },
            )
            print(f"  Inserted {symbol}: {price} {currency}")


def store_exchange_rate(engine, from_currency: str, to_currency: str, rate: float):
    """Insert or update exchange rate for today."""
    today = date.today().isoformat()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                "SELECT id FROM exchange_rates "
                "WHERE from_currency = :from_c AND to_currency = :to_c AND rate_date = :date"
            ),
            {"from_c": from_currency, "to_c": to_currency, "date": today},
        ).fetchone()

        if existing:
            conn.execute(
                text("UPDATE exchange_rates SET rate = :rate WHERE id = :id"),
                {"rate": rate, "id": existing[0]},
            )
            print(f"  Updated {from_currency}->{to_currency}: {rate}")
        else:
            conn.execute(
                text(
                    "INSERT INTO exchange_rates (id, from_currency, to_currency, rate_date, rate, created_at) "
                    "VALUES (:id, :from_c, :to_c, :date, :rate, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "from_c": from_currency,
                    "to_c": to_currency,
                    "date": today,
                    "rate": rate,
                    "now": datetime.utcnow().isoformat(),
                },
            )
            print(f"  Inserted {from_currency}->{to_currency}: {rate}")


def fetch_and_store(engine, ticker: str):
    """Fetch price for a single ticker and store in database."""
    print(f"\nFetching {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Currency pair (e.g., BRL=X -> USD to BRL)
        if "=X" in ticker.upper():
            from_currency = ticker.upper().replace("=X", "")
            rate = info.get("regularMarketPrice")
            if rate is None:
                rate = info.get("previousClose") or info.get("regularMarketOpen")
            if rate:
                store_exchange_rate(engine, from_currency, "BRL", float(rate))
            else:
                print(f"  Warning: No rate found for {ticker}")
            return

        # Regular asset
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        currency = info.get("currency", "USD")

        if price:
            store_asset_price(engine, ticker, float(price), currency)
        else:
            print(f"  Warning: No price found for {ticker}")

    except Exception as e:
        print(f"  Error fetching {ticker}: {e}")


def main():
    args = parse_args()
    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]

    engine = create_engine(args.db_url)

    print(f"Updating prices for {len(tickers)} tickers...")
    print(f"Database: {args.db_url}")

    for ticker in tickers:
        fetch_and_store(engine, ticker)

    print("\nDone!")


if __name__ == "__main__":
    main()