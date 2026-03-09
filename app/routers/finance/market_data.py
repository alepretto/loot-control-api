from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

import httpx

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.finance.asset_price import AssetPrice
from app.models.finance.exchange_rate import ExchangeRate
from app.models.finance.transaction import Currencies

router = APIRouter(prefix="/finance/market-data", tags=["market-data"])


# ─── Response models ──────────────────────────────────────────────────────────

class ExchangeRatesResponse(BaseModel):
    USD: float | None
    EUR: float | None


class AssetPriceItem(BaseModel):
    symbol: str
    price: float
    currency: str


class AssetPricesResponse(BaseModel):
    prices: list[AssetPriceItem]


class ExchangeRateHistoryItem(BaseModel):
    date: str
    USD: float | None
    EUR: float | None


class AssetPriceHistoryItem(BaseModel):
    date: str
    symbol: str
    price: float
    currency: str


class CdiRateItem(BaseModel):
    date: str       # YYYY-MM-DD
    rate_pct: float # daily rate in % (e.g. 0.0406)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/exchange-rates/latest", response_model=ExchangeRatesResponse)
async def get_latest_exchange_rates(
    _: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExchangeRatesResponse:
    usd_result = await session.exec(
        select(ExchangeRate)
        .where(ExchangeRate.currency == Currencies.USD)
        .order_by(ExchangeRate.date.desc())  # type: ignore[union-attr]
        .limit(1)
    )
    usd = usd_result.first()

    eur_result = await session.exec(
        select(ExchangeRate)
        .where(ExchangeRate.currency == Currencies.EUR)
        .order_by(ExchangeRate.date.desc())  # type: ignore[union-attr]
        .limit(1)
    )
    eur = eur_result.first()

    return ExchangeRatesResponse(
        USD=usd.rate if usd else None,
        EUR=eur.rate if eur else None,
    )


@router.get("/asset-prices/latest", response_model=AssetPricesResponse)
async def get_latest_asset_prices(
    _: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AssetPricesResponse:
    result = await session.exec(select(AssetPrice).order_by(AssetPrice.date.desc()))  # type: ignore[union-attr]
    all_prices = result.all()

    seen: set[str] = set()
    latest: list[AssetPriceItem] = []
    for p in all_prices:
        if p.symbol not in seen:
            seen.add(p.symbol)
            latest.append(AssetPriceItem(symbol=p.symbol, price=p.price, currency=p.currency.value))

    return AssetPricesResponse(prices=latest)


@router.get("/exchange-rates/history", response_model=list[ExchangeRateHistoryItem])
async def get_exchange_rate_history(
    _: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ExchangeRateHistoryItem]:
    result = await session.exec(select(ExchangeRate).order_by(ExchangeRate.date))  # type: ignore[union-attr]
    all_rates = result.all()

    by_date: dict[str, dict[str, float | None]] = {}
    for r in all_rates:
        d = str(r.date)
        if d not in by_date:
            by_date[d] = {"USD": None, "EUR": None}
        by_date[d][r.currency.value] = r.rate

    return [
        ExchangeRateHistoryItem(date=d, USD=v["USD"], EUR=v["EUR"])
        for d, v in sorted(by_date.items())
    ]


@router.get("/cdi/history", response_model=list[CdiRateItem])
async def get_cdi_history(
    _: Annotated[str, Depends(get_current_user_id)],
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: str = Query(..., description="YYYY-MM-DD"),
) -> list[CdiRateItem]:
    """Retorna taxas CDI diárias do Banco Central do Brasil (série 12)."""
    from_bcb = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
    to_bcb   = datetime.strptime(date_to,   "%Y-%m-%d").strftime("%d/%m/%Y")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados",
            params={"formato": "json", "dataInicial": from_bcb, "dataFinal": to_bcb},
        )
        resp.raise_for_status()
        data = resp.json()
    return [
        CdiRateItem(
            date=datetime.strptime(item["data"], "%d/%m/%Y").strftime("%Y-%m-%d"),
            rate_pct=float(item["valor"].replace(",", ".")),
        )
        for item in data
    ]


@router.get("/asset-prices/history", response_model=list[AssetPriceHistoryItem])
async def get_asset_price_history(
    _: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AssetPriceHistoryItem]:
    result = await session.exec(select(AssetPrice).order_by(AssetPrice.date, AssetPrice.id))  # type: ignore[union-attr]
    # Deduplicate: keep the last entry per (date, symbol) to handle duplicates from multiple job runs
    seen: dict[tuple[str, str], AssetPrice] = {}
    for p in result.all():
        seen[(str(p.date), p.symbol)] = p
    return [
        AssetPriceHistoryItem(
            date=str(p.date),
            symbol=p.symbol,
            price=p.price,
            currency=p.currency.value,
        )
        for p in sorted(seen.values(), key=lambda x: (str(x.date), x.symbol))
    ]
