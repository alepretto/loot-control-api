from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class CreditCardStatementBase(BaseModel):
    end_date: datetime
    is_paid: bool = Field(default=False)
    total_amount: float | None = None


class CreditCardStatement(CreditCardStatementBase, table=True):
    __tablename__ = "credit_card_statements"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    credit_card_id: UUID = Field(foreign_key="credit_cards.id", index=True)
    end_date: datetime
    is_paid: bool = Field(default=False)
    total_amount: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
