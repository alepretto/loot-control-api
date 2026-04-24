from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class CreditCardBase(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    due_date: int = Field(ge=1, le=31)
    end_date_offset: int = Field(ge=1, le=15)
    is_active: bool = Field(default=True)


class CreditCard(CreditCardBase, table=True):
    __tablename__ = "credit_cards"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    account_id: UUID = Field(foreign_key="accounts.id", index=True)
    label: str
    due_date: int
    end_date_offset: int
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))