from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


# --- Request schemas ---


class AssetPriceCreate(BaseModel):
    symbol: str
    price_date: date
    price: float
    currency: str = "BRL"

    @field_validator("symbol")
    @classmethod
    def symbol_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Symbol must not be empty")
        return v

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v


# --- Response schemas ---


class AssetPriceResponse(BaseModel):
    id: UUID
    symbol: str
    price_date: date
    price: float
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}