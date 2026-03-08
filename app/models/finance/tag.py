import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Tag(SQLModel, table=True):
    __tablename__ = "tags"
    __table_args__ = {"schema": "finance"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    category_id: uuid.UUID = Field(foreign_key="finance.categories.id", index=True)
    name: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
