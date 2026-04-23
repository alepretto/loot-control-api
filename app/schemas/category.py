from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.category import CategoryNature


# --- Request schemas ---


class CategoryCreate(BaseModel):
    label: str
    nature: CategoryNature

    @field_validator("label")
    @classmethod
    def label_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Label must not be empty")
        return v


class CategoryUpdate(BaseModel):
    label: str | None = None
    nature: CategoryNature | None = None


# --- Response schemas ---


class CategoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    label: str
    nature: CategoryNature
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
