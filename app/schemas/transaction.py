from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


# --- Request schemas ---


class TransactionCreate(BaseModel):
    date_transaction: datetime
    type: str  # "outcome" | "income"
    subcategory_id: UUID
    account_id: UUID
    currency_id: UUID
    description: str | None = None
    amount: float
    payment_methods: str | None = None
    statement_id: UUID | None = None
    credit_card_id: UUID | None = None

    @field_validator("type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        if v not in ("outcome", "income"):
            raise ValueError("Type must be 'outcome' or 'income'")
        return v

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("payment_methods")
    @classmethod
    def payment_methods_must_be_valid(cls, v: str | None) -> str | None:
        if v is not None and v not in ("pix", "debit", "credit"):
            raise ValueError("Payment method must be 'pix', 'debit', or 'credit'")
        return v


class TransactionUpdate(BaseModel):
    date_transaction: datetime | None = None
    type: str | None = None
    subcategory_id: UUID | None = None
    account_id: UUID | None = None
    currency_id: UUID | None = None
    description: str | None = None
    amount: float | None = None
    payment_methods: str | None = None
    statement_id: UUID | None = None


# --- Response schemas ---


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    date_transaction: datetime
    type: str
    subcategory_id: UUID
    account_id: UUID
    currency_id: UUID
    description: str | None
    amount: float
    payment_methods: str | None
    statement_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}
