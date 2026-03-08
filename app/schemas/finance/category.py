import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.category import CategoryType


class CategoryCreate(BaseModel):
    name: str
    type: CategoryType


class CategoryRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: CategoryType
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[CategoryType] = None
