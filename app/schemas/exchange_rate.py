from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


# --- Request schemas ---


class ExchangeRateCreate(BaseModel):
    from_currency: str
    to_currency: str = "BRL"
    rate_date: date
    rate: float

    @field_validator("from_currency")
    @classmethod
    def from_currency_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("from_currency must not be empty")
        return v.upper()

    @field_validator("to_currency")
    @classmethod
    def to_currency_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("to_currency must not be empty")
        return v.upper()

    @field_validator("rate")
    @classmethod
    def rate_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("rate must be positive")
        return v


# --- Response schemas ---


class ExchangeRateResponse(BaseModel):
    id: UUID
    from_currency: str
    to_currency: str
    rate_date: date
    rate: float
    created_at: datetime

    model_config = {"from_attributes": True}