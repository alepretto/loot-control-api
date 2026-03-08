import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel


class CategoryType(str, Enum):
    outcome = "outcome"
    income = "income"


class Category(SQLModel, table=True):
    __tablename__ = "categories"  # type: ignore
    __table_args__ = {"schema": "finance"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    family_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            sa.Uuid(),
            ForeignKey("finance.tag_families.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    name: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
