from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class CurrencyCreate(BaseModel):
    label: str
    symbol: str

    @field_validator("label")
    @classmethod
    def label_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Label must not be empty")
        return v

    @field_validator("symbol")
    @classmethod
    def symbol_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Symbol must not be empty")
        return v


class CurrencyUpdate(BaseModel):
    label: str | None = None
    symbol: str | None = None


class CurrencyResponse(BaseModel):
    id: UUID
    label: str
    symbol: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
