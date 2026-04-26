from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class CurrencyCreate(BaseModel):
    code: str
    label: str
    symbol: str

    @field_validator("code")
    @classmethod
    def code_must_be_uppercase(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Code must not be empty")
        return v.strip().upper()

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
    code: str | None = None
    label: str | None = None
    symbol: str | None = None

    @field_validator("code")
    @classmethod
    def code_must_be_uppercase(cls, v: str | None) -> str | None:
        if v is not None:
            if not v.strip():
                raise ValueError("Code must not be empty")
            return v.strip().upper()
        return v


class CurrencyResponse(BaseModel):
    id: UUID
    code: str
    label: str
    symbol: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
