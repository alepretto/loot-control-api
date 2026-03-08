import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    telegram_id: Optional[str] = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    first_name: str
    last_name: str
    telegram_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telegram_id: Optional[str] = None
