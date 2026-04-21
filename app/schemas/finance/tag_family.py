import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.tag_family import FamilyNature


class TagFamilyCreate(BaseModel):
    name: str
    nature: Optional[FamilyNature] = None
    is_active: bool = True


class TagFamilyRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    nature: Optional[FamilyNature]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagFamilyUpdate(BaseModel):
    name: Optional[str] = None
    nature: Optional[FamilyNature] = None
    is_active: Optional[bool] = None
