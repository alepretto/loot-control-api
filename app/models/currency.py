from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class CurrencyBase(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    symbol: str = Field(min_length=1, max_length=10)


class Currency(CurrencyBase, table=True):
    __tablename__ = "currencies"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    label: str
    symbol: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
