from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class SubcategoryBase(BaseModel):
    label: str = Field(min_length=1, max_length=100)


class Subcategory(SubcategoryBase, table=True):
    __tablename__ = "subcategories"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    category_id: UUID = Field(foreign_key="categories.id", index=True)
    label: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
