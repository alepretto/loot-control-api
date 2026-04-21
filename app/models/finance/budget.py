import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.finance.transaction import Currencies


class BudgetPeriod(str, Enum):
    monthly = "monthly"
    yearly = "yearly"


class Budget(SQLModel, table=True):
    __tablename__ = "budgets"
    __table_args__ = (
        sa.CheckConstraint(
            "(family_id IS NOT NULL OR category_id IS NOT NULL) AND "
            "NOT (family_id IS NOT NULL AND category_id IS NOT NULL)",
            name="ck_budgets_family_or_category",
        ),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    family_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("finance.tag_families.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    category_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("finance.categories.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    amount: float
    currency: Currencies = Field(
        default=Currencies.BRL,
        sa_column=Column(
            SAEnum(Currencies, name="currencies", schema="finance", create_type=False),
            nullable=False,
            server_default="BRL",
        ),
    )
    period: BudgetPeriod = Field(
        default=BudgetPeriod.monthly,
        sa_column=Column(
            SAEnum(BudgetPeriod, name="budgetperiod", schema="finance", create_type=False),
            nullable=False,
            server_default="monthly",
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
