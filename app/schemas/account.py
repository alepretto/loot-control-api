from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.account import AccountType


# --- Request schemas ---


class AccountCreate(BaseModel):
    label: str
    type: AccountType
    logo: str | None = None

    @field_validator("label")
    @classmethod
    def label_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Label must not be empty")
        return v


class AccountUpdate(BaseModel):
    label: str | None = None
    type: AccountType | None = None
    logo: str | None = None


# --- Response schemas ---


class AccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    label: str
    type: AccountType
    logo: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
