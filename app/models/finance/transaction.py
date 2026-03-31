import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class Currencies(str, Enum):
    BRL = "BRL"
    USD = "USD"
    EUR = "EUR"


# Shared SAEnum instance — reused by ExchangeRate and AssetPrice to avoid duplicate type registration
currencies_enum = SAEnum(Currencies, name="currencies", schema="finance", create_type=False)


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    __table_args__ = {"schema": "finance"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    tag_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            ForeignKey("finance.tags.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    date_transaction: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    value: float
    currency: Currencies = Field(
        sa_column=Column(
            SAEnum(Currencies, name="currencies", schema="finance", create_type=True),
            nullable=False,
        )
    )
    payment_method_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(),
            ForeignKey("finance.payment_methods.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    quantity: Optional[float] = Field(default=None)
    symbol: Optional[str] = Field(default=None)
    index_rate: Optional[float] = Field(default=None)
    index: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
