import uuid
from datetime import date
from typing import List

import httpx

from app.core.database import AsyncSessionLocal
from app.models.finance.asset_price import AssetPrice
from app.models.finance.transaction import Currencies

COINGECKO_API = "https://api.coingecko.com/api/v3"
BRAPI_API = "https://brapi.dev/api"


async def fetch_crypto_prices(symbols: List[str]) -> List[AssetPrice]:
    ids = ",".join(symbols)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{COINGECKO_API}/simple/price",
            params={"ids": ids, "vs_currencies": "usd,brl"},
        )
        response.raise_for_status()
        data = response.json()

    today = date.today()
    return [
        AssetPrice(
            id=uuid.uuid4(),
            symbol=symbol.upper(),
            price=values.get("usd", 0),
            currency=Currencies.USD,
            date=today,
        )
        for symbol, values in data.items()
    ]


async def fetch_br_stock_prices(tickers: List[str]) -> List[AssetPrice]:
    ticker_str = ",".join(tickers)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BRAPI_API}/quote/{ticker_str}")
        response.raise_for_status()
        data = response.json()

    today = date.today()
    return [
        AssetPrice(
            id=uuid.uuid4(),
            symbol=result["symbol"],
            price=result["regularMarketPrice"],
            currency=Currencies.BRL,
            date=today,
        )
        for result in data.get("results", [])
    ]


async def update_asset_prices() -> None:
    crypto_prices = await fetch_crypto_prices(["bitcoin", "ethereum", "solana"])
    br_prices = await fetch_br_stock_prices(["PETR4", "VALE3", "ITUB4"])

    async with AsyncSessionLocal() as session:
        for price in [*crypto_prices, *br_prices]:
            session.add(price)
        await session.commit()
