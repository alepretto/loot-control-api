from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class InvestmentLedger(BaseModel, table=True):
    __tablename__ = "investment_ledger"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    transaction_id: UUID = Field(foreign_key="transactions.id", index=True)
    symbol: str = Field(min_length=1, max_length=20)
    quantity: float
    index: str | None = None
    index_rate: float | None = None
    currency: str = Field(default="BRL", max_length=10)
    purchase_exchange_rate: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
