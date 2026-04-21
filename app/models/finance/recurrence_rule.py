import uuid
from datetime import UTC, date, datetime
from enum import Enum
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class RecurrenceFrequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class RecurrenceRule(SQLModel, table=True):
    __tablename__ = "recurrence_rules"
    __table_args__ = {"schema": "finance"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str
    frequency: RecurrenceFrequency = Field(
        sa_column=Column(
            SAEnum(RecurrenceFrequency, name="recurrencefrequency", schema="finance", create_type=False),
            nullable=False,
        )
    )
    interval: int = Field(default=1)
    start_date: date
    end_date: Optional[date] = Field(default=None)
    template_transaction: dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False)
    )
    is_active: bool = Field(default=True)
    last_generated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
