import uuid
from datetime import date

import httpx

from app.core.database import AsyncSessionLocal
from app.models.finance.exchange_rate import ExchangeRate
from app.models.finance.transaction import Currencies

AWESOME_API_URL = "https://economia.awesomeapi.com.br/json/last"


async def update_exchange_rates() -> None:
    pairs = ["USD-BRL", "EUR-BRL"]
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AWESOME_API_URL}/{','.join(pairs)}")
        response.raise_for_status()
        data = response.json()

    today = date.today()
    mapping = {"USDBRL": Currencies.USD, "EURBRL": Currencies.EUR}

    async with AsyncSessionLocal() as session:
        for key, currency in mapping.items():
            if key in data:
                rate = float(data[key]["bid"])
                session.add(ExchangeRate(id=uuid.uuid4(), currency=currency, rate=rate, date=today))
        await session.commit()
