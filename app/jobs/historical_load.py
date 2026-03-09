"""Carga histórica de cotações de câmbio e preços de ativos.

Fontes:
  - Exchange rates: AwesomeAPI (USD/BRL, EUR/BRL)
  - Crypto: Binance klines (USDT pairs) — sem key, sem rate limit agressivo
  - Ações BR: Yahoo Finance com sufixo .SA (PETR4.SA)
  - Stocks EUA: Yahoo Finance
"""

import asyncio
import logging
import uuid
from datetime import date, datetime, timezone
from typing import List

import httpx

from app.core.database import AsyncSessionLocal
from app.jobs.asset_prices import CRYPTO_ID_MAP, _get_distinct_symbols, _is_br_stock, _is_crypto, _is_us_stock
from app.models.finance.asset_price import AssetPrice
from app.models.finance.exchange_rate import ExchangeRate
from app.models.finance.transaction import Currencies

logger = logging.getLogger(__name__)

AWESOME_API_URL = "https://economia.awesomeapi.com.br/json/daily"
BINANCE_API     = "https://api.binance.com/api/v3"
YAHOO_API       = "https://query1.finance.yahoo.com/v8/finance/chart"

YF_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _existing_exchange_rates() -> set[tuple[str, date]]:
    async with AsyncSessionLocal() as session:
        from sqlmodel import select
        result = await session.exec(select(ExchangeRate.currency, ExchangeRate.date))
        return {(r[0].value, r[1]) for r in result.all()}


async def _existing_asset_prices() -> set[tuple[str, date]]:
    async with AsyncSessionLocal() as session:
        from sqlmodel import select
        result = await session.exec(select(AssetPrice.symbol, AssetPrice.date))
        return {(r[0], r[1]) for r in result.all()}


async def _save(records: list) -> None:
    if not records:
        return
    async with AsyncSessionLocal() as session:
        for r in records:
            session.add(r)
        await session.commit()


def _ts_to_date(ts: int | float) -> date:
    return datetime.fromtimestamp(ts, tz=timezone.utc).date()


def _date_to_ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


# ─── Exchange rates ────────────────────────────────────────────────────────────

async def load_historical_exchange_rates(date_from: date, date_to: date) -> dict:
    existing     = await _existing_exchange_rates()
    days_needed  = (date.today() - date_from).days + 10
    pairs        = [("USD-BRL", Currencies.USD), ("EUR-BRL", Currencies.EUR)]
    new_records: list[ExchangeRate] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for pair, currency in pairs:
            try:
                resp = await client.get(f"{AWESOME_API_URL}/{pair}/{min(days_needed, 3000)}")
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, list):
                    logger.error("AwesomeAPI resposta inesperada para %s: %s", pair, data)
                    continue
            except Exception as e:
                logger.error("AwesomeAPI erro %s: %s", pair, e)
                continue

            for item in data:
                try:
                    d = _ts_to_date(int(item["timestamp"]))
                    if d < date_from or d > date_to:
                        continue
                    if (currency.value, d) in existing:
                        continue
                    new_records.append(ExchangeRate(
                        id=uuid.uuid4(), currency=currency, rate=float(item["bid"]), date=d,
                    ))
                    existing.add((currency.value, d))
                except (KeyError, ValueError) as e:
                    logger.debug("AwesomeAPI item inválido: %s", e)

    await _save(new_records)
    logger.info("Exchange rates histórico: %d novos registros", len(new_records))
    return {"loaded": len(new_records), "pairs": [p for p, _ in pairs]}


# ─── Crypto via Binance klines ────────────────────────────────────────────────

async def _fetch_binance_daily(client: httpx.AsyncClient, symbol: str, start_ms: int, end_ms: int) -> list[tuple[date, float]]:
    """Fetches daily close prices from Binance. Paginates if needed (max 1000 candles/request)."""
    results: list[tuple[date, float]] = []
    current = start_ms

    while current <= end_ms:
        try:
            resp = await client.get(
                f"{BINANCE_API}/klines",
                params={"symbol": f"{symbol}USDT", "interval": "1d", "startTime": current, "endTime": end_ms, "limit": 1000},
            )
            if resp.status_code == 400:
                # Invalid symbol
                logger.warning("Binance: símbolo inválido %sUSDT", symbol)
                break
            resp.raise_for_status()
            candles = resp.json()
        except Exception as e:
            logger.error("Binance erro %s: %s", symbol, e)
            break

        if not candles:
            break

        for c in candles:
            # [openTime, open, high, low, close, volume, closeTime, ...]
            try:
                d     = _ts_to_date(c[0] / 1000)
                close = float(c[4])
                results.append((d, close))
            except (IndexError, ValueError):
                continue

        # Last candle's open time + 1 day to avoid overlap
        last_open_ms = candles[-1][0]
        if last_open_ms >= end_ms or len(candles) < 1000:
            break
        current = last_open_ms + 86_400_000  # +1 day in ms

    return results


async def load_historical_crypto_prices(symbols: List[str], date_from: date, date_to: date) -> dict:
    existing  = await _existing_asset_prices()
    start_ms  = _date_to_ms(date_from)
    end_ms    = _date_to_ms(date_to) + 86_400_000 - 1
    new_records: list[AssetPrice] = []

    async with httpx.AsyncClient(timeout=60) as client:
        for sym in symbols:
            candles = await _fetch_binance_daily(client, sym.upper(), start_ms, end_ms)
            if not candles:
                logger.warning("Sem dados Binance para %s — verifique se o par %sUSDT existe", sym, sym.upper())
                continue
            for d, price in candles:
                if (sym.upper(), d) in existing:
                    continue
                new_records.append(AssetPrice(
                    id=uuid.uuid4(), symbol=sym.upper(), price=price,
                    currency=Currencies.USD, date=d,
                ))
                existing.add((sym.upper(), d))
            await asyncio.sleep(0.2)  # Binance rate limit: 1200 req/min

    await _save(new_records)
    logger.info("Crypto histórico (Binance): %d novos registros para %s", len(new_records), symbols)
    return {"loaded": len(new_records), "symbols": symbols}


# ─── Yahoo Finance helper ─────────────────────────────────────────────────────

async def _fetch_yahoo_daily(
    client: httpx.AsyncClient,
    symbol: str,
    from_ts: int,
    to_ts: int,
) -> list[tuple[date, float]]:
    try:
        resp = await client.get(
            f"{YAHOO_API}/{symbol}",
            params={"period1": from_ts, "period2": to_ts, "interval": "1d"},
            headers=YF_HEADERS,
        )
        resp.raise_for_status()
        chart = resp.json().get("chart", {}).get("result", [])
    except Exception as e:
        logger.error("Yahoo Finance erro %s: %s", symbol, e)
        return []

    if not chart:
        logger.warning("Yahoo Finance sem resultado para %s", symbol)
        return []

    timestamps = chart[0].get("timestamp", [])
    closes     = chart[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
    return [(d, float(p)) for ts, p in zip(timestamps, closes) if p is not None and (d := _ts_to_date(ts))]


# ─── BR stocks via Yahoo Finance (.SA suffix) ─────────────────────────────────

async def load_historical_br_stock_prices(tickers: List[str], date_from: date, date_to: date) -> dict:
    existing = await _existing_asset_prices()
    from_ts  = int(datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc).timestamp())
    to_ts    = int(datetime(date_to.year,   date_to.month,   date_to.day,   23, 59, 59, tzinfo=timezone.utc).timestamp())
    new_records: list[AssetPrice] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for ticker in tickers:
            yf_symbol = f"{ticker}.SA"
            candles   = await _fetch_yahoo_daily(client, yf_symbol, from_ts, to_ts)
            for d, price in candles:
                if d < date_from or d > date_to:
                    continue
                if (ticker, d) in existing:
                    continue
                new_records.append(AssetPrice(
                    id=uuid.uuid4(), symbol=ticker, price=price,
                    currency=Currencies.BRL, date=d,
                ))
                existing.add((ticker, d))
            await asyncio.sleep(0.3)

    await _save(new_records)
    logger.info("BR stocks histórico (Yahoo): %d novos registros para %s", len(new_records), tickers)
    return {"loaded": len(new_records), "tickers": tickers}


# ─── US stocks via Yahoo Finance ──────────────────────────────────────────────

async def load_historical_us_stock_prices(tickers: List[str], date_from: date, date_to: date) -> dict:
    existing = await _existing_asset_prices()
    from_ts  = int(datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc).timestamp())
    to_ts    = int(datetime(date_to.year,   date_to.month,   date_to.day,   23, 59, 59, tzinfo=timezone.utc).timestamp())
    new_records: list[AssetPrice] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for ticker in tickers:
            candles = await _fetch_yahoo_daily(client, ticker, from_ts, to_ts)
            for d, price in candles:
                if d < date_from or d > date_to:
                    continue
                if (ticker, d) in existing:
                    continue
                new_records.append(AssetPrice(
                    id=uuid.uuid4(), symbol=ticker, price=price,
                    currency=Currencies.USD, date=d,
                ))
                existing.add((ticker, d))
            await asyncio.sleep(0.3)

    await _save(new_records)
    logger.info("US stocks histórico (Yahoo): %d novos registros para %s", len(new_records), tickers)
    return {"loaded": len(new_records), "tickers": tickers}


# ─── Orchestrator ─────────────────────────────────────────────────────────────

async def run_historical_load(date_from: date, date_to: date) -> dict:
    symbols     = await _get_distinct_symbols()
    crypto_syms = [s for s in symbols if _is_crypto(s)]
    br_syms     = [s for s in symbols if _is_br_stock(s)]
    us_syms     = [s for s in symbols if _is_us_stock(s)]

    logger.info("Carga histórica %s → %s | crypto=%s BR=%s US=%s", date_from, date_to, crypto_syms, br_syms, us_syms)

    fx     = await load_historical_exchange_rates(date_from, date_to)
    crypto = await load_historical_crypto_prices(crypto_syms, date_from, date_to)
    br     = await load_historical_br_stock_prices(br_syms, date_from, date_to)
    us     = await load_historical_us_stock_prices(us_syms, date_from, date_to)

    return {"exchange_rates": fx, "crypto": crypto, "br_stocks": br, "us_stocks": us}
