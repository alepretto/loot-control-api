import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class CategoryType(str, Enum):
    outcome = "outcome"
    income = "income"


class Category(SQLModel, table=True):
    __tablename__ = "categories"
    __table_args__ = {"schema": "finance"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    type: CategoryType = Field(
        sa_column=Column(
            SAEnum(CategoryType, name="categorytype", schema="finance"),
            nullable=False,
        )
    )
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
