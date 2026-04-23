from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


# --- Request schemas ---


class SubcategoryCreate(BaseModel):
    label: str
    category_id: UUID
    is_active: bool = True

    @field_validator("label")
    @classmethod
    def label_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Label must not be empty")
        return v


class SubcategoryUpdate(BaseModel):
    label: str | None = None
    category_id: UUID | None = None
    is_active: bool | None = None


# --- Response schemas ---


class SubcategoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    category_id: UUID
    label: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
