import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TagFamilyCreate(BaseModel):
    name: str


class TagFamilyRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagFamilyUpdate(BaseModel):
    name: Optional[str] = None
