import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class IncomeType(str, Enum):
    active = "active"
    passive = "passive"
    sporadic = "sporadic"


class Tag(SQLModel, table=True):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "name", name="uq_tags_user_category_name"),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    category_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            ForeignKey("finance.categories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    name: str
    is_active: bool = Field(default=True)
    income_type: Optional[IncomeType] = Field(
        default=None,
        sa_column=Column(
            SAEnum(IncomeType, name="incometype", schema="finance", create_type=False),
            nullable=True,
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
