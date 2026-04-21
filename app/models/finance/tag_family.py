import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class FamilyNature(str, Enum):
    fixed_expense = "fixed_expense"
    variable_expense = "variable_expense"
    income = "income"
    investment = "investment"


class TagFamily(SQLModel, table=True):
    __tablename__ = "tag_families"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tag_families_user_name"),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str
    nature: Optional[FamilyNature] = Field(
        default=None,
        sa_column=Column(
            SAEnum(FamilyNature, name="familynature", schema="finance", create_type=False),
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
