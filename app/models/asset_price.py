from datetime import date, datetime, timezone
from uuid import UUID

from sqlmodel import Field, UniqueConstraint
import uuid6

from app.models.base import BaseModel


class AssetPrice(BaseModel, table=True):
    __tablename__ = "asset_prices"
    __table_args__ = (UniqueConstraint("symbol", "price_date", name="uq_asset_price_symbol_date"),)

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    symbol: str = Field(max_length=20, index=True)
    price_date: date = Field(index=True)
    price: float
    currency: str = Field(default="BRL", max_length=10)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))