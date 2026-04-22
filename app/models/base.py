from uuid import UUID

from sqlmodel import Field, SQLModel
import uuid6


class BaseModel(SQLModel):
    """Base model with UUID v7 primary key for all tables."""

    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)