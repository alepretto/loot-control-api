from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


# --- Request schemas ---


class InvestmentLedgerCreate(BaseModel):
    transaction_id: UUID
    symbol: str
    quantity: float
    index: str | None = None
    index_rate: float | None = None

    @field_validator("symbol")
    @classmethod
    def symbol_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Symbol must not be empty")
        return v

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v


class InvestmentLedgerUpdate(BaseModel):
    transaction_id: UUID | None = None
    symbol: str | None = None
    quantity: float | None = None
    index: str | None = None
    index_rate: float | None = None


# --- Response schemas ---


class InvestmentLedgerResponse(BaseModel):
    id: UUID
    user_id: UUID
    transaction_id: UUID
    symbol: str
    quantity: float
    index: str | None
    index_rate: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
