import logging
import uuid
from datetime import date
from typing import List

import httpx
from sqlmodel import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.finance.asset_price import AssetPrice
from app.models.finance.transaction import Currencies, Transaction

logger = logging.getLogger(__name__)

COINGECKO_API = "https://api.coingecko.com/api/v3"
BRAPI_API = "https://brapi.dev/api"

# Mapeamento símbolo (uppercase) → CoinGecko ID
CRYPTO_ID_MAP: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "MATIC": "matic-network",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "LTC": "litecoin",
    "ATOM": "cosmos",
    "XLM": "stellar",
    "ALGO": "algorand",
    "NEAR": "near",
    "FTM": "fantom",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "FET":  "fetch-ai",
    "SUI":  "sui",
    "TON":  "the-open-network",
    "ARB":  "arbitrum",
    "OP":   "optimism",
    "INJ":  "injective-protocol",
    "TIA":  "celestia",
    "SEI":  "sei-network",
}


def _is_br_stock(symbol: str) -> bool:
    """Ações BR terminam em dígito (ex: PETR4, VALE3, MXRF11)."""
    return len(symbol) >= 4 and symbol[-1].isdigit()


def _is_crypto(symbol: str) -> bool:
    return symbol.upper() in CRYPTO_ID_MAP


def _is_us_stock(symbol: str) -> bool:
    """US stocks não são crypto nem BR stock."""
    return not _is_crypto(symbol) and not _is_br_stock(symbol)


async def _get_distinct_symbols() -> list[str]:
    """Retorna símbolos distintos de transações de mercado (exclui renda fixa com index preenchido)."""
    async with AsyncSessionLocal() as session:
        result = await session.exec(
            select(Transaction.symbol)
            .where(
                Transaction.symbol.isnot(None),  # type: ignore[union-attr]
                Transaction.index.is_(None),      # renda fixa tem index — ignorar
            )
            .distinct()
        )
        return [s for s in result.all() if s is not None]


async def fetch_crypto_prices(symbols: List[str]) -> List[AssetPrice]:
    """Busca preços no CoinGecko para os símbolos fornecidos."""
    coingecko_ids = []
    symbol_by_id: dict[str, str] = {}

    for sym in symbols:
        cg_id = CRYPTO_ID_MAP.get(sym.upper())
        if cg_id:
            coingecko_ids.append(cg_id)
            symbol_by_id[cg_id] = sym.upper()
        else:
            logger.warning("Símbolo cripto sem mapeamento CoinGecko: %s (ignorado)", sym)

    if not coingecko_ids:
        return []

    headers = {}
    if settings.COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY

    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            response = await client.get(
                f"{COINGECKO_API}/simple/price",
                params={"ids": ",".join(coingecko_ids), "vs_currencies": "usd,brl"},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.error("Erro ao buscar preços cripto: %s", e)
        return []

    today = date.today()
    prices = []
    for cg_id, values in data.items():
        sym: str = symbol_by_id.get(cg_id) or cg_id.upper()
        usd_price = values.get("usd")
        if usd_price is not None:
            prices.append(AssetPrice(
                id=uuid.uuid4(),
                symbol=sym,
                price=usd_price,
                currency=Currencies.USD,
                date=today,
            ))
    return prices


async def fetch_us_stock_prices(tickers: List[str]) -> List[AssetPrice]:
    """Busca preços via Yahoo Finance para ações dos EUA."""
    if not tickers:
        return []

    today = date.today()
    prices = []

    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as client:
        for ticker in tickers:
            try:
                response = await client.get(
                    "https://query1.finance.yahoo.com/v7/finance/quote",
                    params={"symbols": ticker},
                )
                if response.status_code == 404:
                    logger.warning("Ticker não encontrado no Yahoo Finance: %s (ignorado)", ticker)
                    continue
                response.raise_for_status()
                data = response.json()
                results = data.get("quoteResponse", {}).get("result", [])
                for r in results:
                    if "regularMarketPrice" in r:
                        prices.append(AssetPrice(
                            id=uuid.uuid4(),
                            symbol=r["symbol"],
                            price=r["regularMarketPrice"],
                            currency=Currencies.USD,
                            date=today,
                        ))
            except httpx.HTTPStatusError as e:
                logger.warning("Erro HTTP ao buscar %s: %s (ignorado)", ticker, e)
            except Exception as e:
                logger.error("Erro ao buscar preço de %s: %s", ticker, e)

    return prices


async def fetch_br_stock_prices(tickers: List[str]) -> List[AssetPrice]:
    """Busca preços via brapi.dev para ações brasileiras."""
    if not tickers:
        return []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{BRAPI_API}/quote/{','.join(tickers)}")
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.error("Erro ao buscar preços ações BR: %s", e)
        return []

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
        if "regularMarketPrice" in result
    ]


async def _delete_asset_prices_today(symbols: list[str]) -> None:
    """Remove preços de hoje para os símbolos fornecidos (permite re-fetch no mesmo dia)."""
    today = date.today()
    symbols_upper = [s.upper() for s in symbols]
    async with AsyncSessionLocal() as session:
        existing = await session.exec(
            select(AssetPrice).where(
                AssetPrice.date == today,  # type: ignore[arg-type]
                AssetPrice.symbol.in_(symbols_upper),  # type: ignore[union-attr]
            )
        )
        for row in existing.all():
            await session.delete(row)
        await session.commit()


async def update_asset_prices() -> None:
    """Job principal: descobre ativos investidos e atualiza preços.

    Roda até 3x/dia — apaga os registros de hoje antes de inserir novos.
    """
    symbols = await _get_distinct_symbols()

    if not symbols:
        logger.info("Nenhum ativo encontrado nas transações.")
        return

    logger.info("Ativos encontrados nas transações: %s", symbols)

    await _delete_asset_prices_today(symbols)

    crypto_symbols = [s for s in symbols if _is_crypto(s)]
    br_symbols = [s for s in symbols if _is_br_stock(s)]
    us_symbols = [s for s in symbols if _is_us_stock(s)]

    logger.info("Classificação — crypto: %s, BR: %s, US: %s", crypto_symbols, br_symbols, us_symbols)

    crypto_prices = await fetch_crypto_prices(crypto_symbols)
    br_prices = await fetch_br_stock_prices(br_symbols)
    us_prices = await fetch_us_stock_prices(us_symbols)

    all_prices = [*crypto_prices, *br_prices, *us_prices]

    if not all_prices:
        logger.warning("Nenhum preço retornado pelas APIs.")
        return

    async with AsyncSessionLocal() as session:
        for price in all_prices:
            session.add(price)
        await session.commit()

    logger.info(
        "Preços atualizados: %d cripto, %d ações BR, %d US stocks",
        len(crypto_prices),
        len(br_prices),
        len(us_prices),
    )
