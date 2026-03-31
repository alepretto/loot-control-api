import uuid
from datetime import UTC, datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class PaymentMethodCategory(str, Enum):
    money = "money"
    benefit = "benefit"


class PaymentMethod(SQLModel, table=True):
    __tablename__ = "payment_methods"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "name", name="uq_payment_methods_user_name"),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str
    category: PaymentMethodCategory = Field(
        sa_column=Column(
            SAEnum(PaymentMethodCategory, name="paymentmethodcategory", schema="finance", create_type=False),
            nullable=False,
        )
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
