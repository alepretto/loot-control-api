import uuid
from datetime import datetime, UTC
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Text


class AgentMessage(SQLModel, table=True):
    __tablename__ = "messages"
    __table_args__ = {"schema": "agent"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(nullable=False, index=True)
    role: str = Field(nullable=False)  # "user" | "assistant"
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
