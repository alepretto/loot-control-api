from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Field
import uuid6

from app.models.base import BaseModel


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")


class User(UserBase, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True, index=True)
    password: str  # hashed password
    role: str = Field(default="user")  # "user" | "admin"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))