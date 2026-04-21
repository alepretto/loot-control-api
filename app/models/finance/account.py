import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.finance.transaction import Currencies


class AccountType(str, Enum):
    checking = "checking"
    savings = "savings"
    broker = "broker"
    digital = "digital"
    wallet = "wallet"
    benefit = "benefit"
    credit_card = "credit_card"


class BalanceMode(str, Enum):
    calculated = "calculated"
    manual = "manual"


class Account(SQLModel, table=True):
    __tablename__ = "accounts"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "name", name="uq_accounts_user_name"),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str
    type: AccountType = Field(
        sa_column=Column(
            SAEnum(AccountType, name="accounttype", schema="finance", create_type=False),
            nullable=False,
        )
    )
    institution: Optional[str] = Field(default=None)
    currency: Currencies = Field(
        default=Currencies.BRL,
        sa_column=Column(
            SAEnum(Currencies, name="currencies", schema="finance", create_type=False),
            nullable=False,
            server_default="BRL",
        ),
    )
    balance_mode: BalanceMode = Field(
        default=BalanceMode.calculated,
        sa_column=Column(
            SAEnum(BalanceMode, name="balancemode", schema="finance", create_type=False),
            nullable=False,
            server_default="calculated",
        ),
    )
    manual_balance: Optional[float] = Field(default=None)
    credit_limit: Optional[float] = Field(default=None)
    closing_day: Optional[int] = Field(default=None)
    due_day: Optional[int] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
