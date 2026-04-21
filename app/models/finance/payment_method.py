import uuid
from datetime import UTC, datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class PaymentMethodType(str, Enum):
    debit = "debit"
    credit = "credit"
    benefit = "benefit"


class PaymentMethod(SQLModel, table=True):
    __tablename__ = "payment_methods"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "account_id", "name", name="uq_payment_methods_user_account_name"),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str
    type: PaymentMethodType = Field(
        sa_column=Column(
            SAEnum(PaymentMethodType, name="paymentmethodtype", schema="finance", create_type=False),
            nullable=False,
        )
    )
    account_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            ForeignKey("finance.accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )