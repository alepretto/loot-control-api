from datetime import date, datetime, timezone
from uuid import UUID

from sqlmodel import Field, UniqueConstraint
import uuid6

from app.models.base import BaseModel


class ExchangeRate(BaseModel, table=True):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint(
            "from_currency", "to_currency", "rate_date",
            name="uq_exchange_rate_from_to_date",
        ),
    )

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    from_currency: str = Field(max_length=10, index=True)
    to_currency: str = Field(default="BRL", max_length=10, index=True)
    rate_date: date = Field(index=True)
    rate: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))