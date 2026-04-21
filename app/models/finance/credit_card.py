import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel


class CreditCard(SQLModel, table=True):
    __tablename__ = "credit_cards"
    __table_args__ = (
        sa.UniqueConstraint("payment_method_id", name="uq_credit_cards_payment_method"),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    payment_method_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            ForeignKey("finance.payment_methods.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str
    limit_amount: float
    due_day: int
    closing_offset: int = Field(default=3)
    current_balance: float = Field(default=0.0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    @property
    def closing_day(self) -> int:
        return max(1, self.due_day - self.closing_offset)