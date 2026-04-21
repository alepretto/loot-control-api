import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.tag import IncomeType


class TagCreate(BaseModel):
    name: str
    category_id: uuid.UUID
    is_active: bool = True
    income_type: Optional[IncomeType] = None


class TagRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID
    name: str
    is_active: bool
    income_type: Optional[IncomeType]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[uuid.UUID] = None
    income_type: Optional[IncomeType] = None
