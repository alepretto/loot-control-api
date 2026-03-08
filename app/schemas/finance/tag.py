import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.category import CategoryType


class TagCreate(BaseModel):
    name: str
    category_id: uuid.UUID
    type: CategoryType
    is_active: bool = True


class TagRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID
    type: CategoryType
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[CategoryType] = None
    is_active: Optional[bool] = None
