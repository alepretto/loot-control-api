from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class Transaction(BaseModel, table=True):
    __tablename__ = "transactions"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    date_transaction: datetime
    type: str  # "outcome" | "income"
    subcategory_id: UUID = Field(foreign_key="subcategories.id", index=True)
    account_id: UUID = Field(foreign_key="accounts.id", index=True)
    currency_id: UUID = Field(foreign_key="currencies.id", index=True)
    description: str | None = None
    amount: float
    payment_methods: str | None = None  # "pix" | "debit" | "credit"
    statement_id: UUID | None = Field(foreign_key="credit_card_statements.id", index=True, default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
