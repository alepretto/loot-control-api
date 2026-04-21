import uuid
from datetime import UTC, date, datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class LiabilityType(str, Enum):
    financing = "financing"
    loan = "loan"
    other = "other"


class LiabilityIndex(str, Enum):
    CDI = "CDI"
    IPCA = "IPCA"
    fixed = "fixed"
    none = "none"


class Liability(SQLModel, table=True):
    __tablename__ = "liabilities"
    __table_args__ = {"schema": "finance"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str
    type: LiabilityType = Field(
        sa_column=Column(
            SAEnum(LiabilityType, name="liabilitytype", schema="finance", create_type=False),
            nullable=False,
        )
    )
    institution: Optional[str] = Field(default=None)
    total_value: float
    outstanding_balance: float
    monthly_payment: Optional[float] = Field(default=None)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    interest_rate: Optional[float] = Field(default=None)
    index: Optional[LiabilityIndex] = Field(
        default=None,
        sa_column=Column(
            SAEnum(LiabilityIndex, name="liabilityindex", schema="finance", create_type=False),
            nullable=True,
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
