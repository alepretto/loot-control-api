from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


# --- Request schemas ---


class CreditCardCreate(BaseModel):
    account_id: UUID
    label: str
    due_date: int
    end_date_offset: int
    is_active: bool = True

    @field_validator("label")
    @classmethod
    def label_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Label must not be empty")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_must_be_valid(cls, v: int) -> int:
        if v < 1 or v > 31:
            raise ValueError("Due date must be between 1 and 31")
        return v

    @field_validator("end_date_offset")
    @classmethod
    def end_date_offset_must_be_valid(cls, v: int) -> int:
        if v < 1 or v > 15:
            raise ValueError("End date offset must be between 1 and 15")
        return v


class CreditCardUpdate(BaseModel):
    account_id: UUID | None = None
    label: str | None = None
    due_date: int | None = None
    end_date_offset: int | None = None
    is_active: bool | None = None


# --- Response schemas ---


class CreditCardResponse(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    label: str
    due_date: int
    end_date_offset: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}