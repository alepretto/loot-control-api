import uuid
from datetime import UTC, date, datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class InvoiceStatus(str, Enum):
    open = "open"
    closed = "closed"
    paid = "paid"


class Invoice(SQLModel, table=True):
    __tablename__ = "invoices"
    __table_args__ = (
        sa.UniqueConstraint("credit_card_id", "reference_month", name="uq_invoices_credit_card_month"),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    credit_card_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid(),
            sa.ForeignKey("finance.credit_cards.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    reference_month: str = Field(max_length=7)  # YYYY-MM
    closing_date: date
    due_date: date
    total_amount: float = Field(default=0.0)
    status: InvoiceStatus = Field(
        default=InvoiceStatus.open,
        sa_column=Column(
            SAEnum(InvoiceStatus, name="invoicestatus", schema="finance", create_type=False),
            nullable=False,
            server_default="open",
        ),
    )
    paid_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )