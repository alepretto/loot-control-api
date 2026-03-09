from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.core.database import AsyncSessionLocal
from app.core.security import require_admin
from app.jobs.asset_prices import update_asset_prices
from app.jobs.exchange_rates import update_exchange_rates
from app.jobs.historical_load import run_historical_load
from app.jobs.scheduler import scheduler
from app.models.finance.asset_price import AssetPrice
from app.models.finance.exchange_rate import ExchangeRate

router = APIRouter(prefix="/admin", tags=["admin"])

JOB_REGISTRY = {
    "exchange_rates": update_exchange_rates,
    "asset_prices": update_asset_prices,
}

JOB_META = {
    "exchange_rates": {
        "name": "Exchange Rates",
        "description": "Cotações USD/EUR → BRL via AwesomeAPI",
        "schedule": "Diário às 21:00 UTC",
    },
    "asset_prices": {
        "name": "Asset Prices",
        "description": "Preços cripto (CoinGecko) + ações BR (brapi.dev)",
        "schedule": "Diário às 21:30 UTC",
    },
}


class JobStatus(BaseModel):
    id: str
    name: str
    description: str
    schedule: str
    next_run_time: Optional[str]
    last_run_date: Optional[date]


class JobsResponse(BaseModel):
    jobs: list[JobStatus]


class RunJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class HistoricalLoadRequest(BaseModel):
    date_from: date
    date_to: date


class HistoricalLoadResult(BaseModel):
    exchange_rates: dict
    crypto: dict
    br_stocks: dict
    us_stocks: dict


async def _get_last_run_dates() -> dict[str, Optional[date]]:
    async with AsyncSessionLocal() as session:
        er_result = await session.exec(select(ExchangeRate.date).order_by(ExchangeRate.date.desc()).limit(1))  # type: ignore[union-attr]
        er_date = er_result.first()

        ap_result = await session.exec(select(AssetPrice.date).order_by(AssetPrice.date.desc()).limit(1))  # type: ignore[union-attr]
        ap_date = ap_result.first()

    return {
        "exchange_rates": er_date,
        "asset_prices": ap_date,
    }


@router.get("/jobs", response_model=JobsResponse)
async def list_jobs(
    _: Annotated[str, Depends(require_admin)],
) -> JobsResponse:
    last_runs = await _get_last_run_dates()
    jobs = []
    for job_id, meta in JOB_META.items():
        apscheduler_job = scheduler.get_job(job_id)
        next_run = (
            apscheduler_job.next_run_time.isoformat() if apscheduler_job and apscheduler_job.next_run_time else None
        )
        jobs.append(
            JobStatus(
                id=job_id,
                name=meta["name"],
                description=meta["description"],
                schedule=meta["schedule"],
                next_run_time=next_run,
                last_run_date=last_runs.get(job_id),
            )
        )
    return JobsResponse(jobs=jobs)


@router.post("/jobs/{job_id}/run", response_model=RunJobResponse)
async def run_job(
    job_id: str,
    _: Annotated[str, Depends(require_admin)],
) -> RunJobResponse:
    fn = JOB_REGISTRY.get(job_id)
    if fn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' não encontrado")

    try:
        await fn()
        return RunJobResponse(job_id=job_id, status="success", message="Job executado com sucesso")
    except Exception as e:
        return RunJobResponse(job_id=job_id, status="error", message=str(e))


@router.post("/historical-load", response_model=HistoricalLoadResult)
async def historical_load(
    body: HistoricalLoadRequest,
    _: Annotated[str, Depends(require_admin)],
) -> HistoricalLoadResult:
    result = await run_historical_load(body.date_from, body.date_to)
    return HistoricalLoadResult(**result)
