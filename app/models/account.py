from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class AccountType(StrEnum):
    bank = "bank"
    wallet = "wallet"
    digital = "digital"
    benefits = "benefits"


class AccountBase(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    type: AccountType
    logo: str | None = None


class Account(AccountBase, table=True):
    __tablename__ = "accounts"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    label: str
    type: AccountType
    logo: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
