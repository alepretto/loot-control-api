from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class CategoryNature(StrEnum):
    fixed = "fixed"
    variable = "variable"
    investment = "investment"
    revenue = "revenue"


class CategoryBase(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    nature: CategoryNature


class Category(CategoryBase, table=True):
    __tablename__ = "categories"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    label: str
    nature: CategoryNature
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
