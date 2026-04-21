import uuid
from datetime import UTC, date, datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class NetWorthSnapshot(SQLModel, table=True):
    __tablename__ = "net_worth_snapshots"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "date", name="uq_net_worth_snapshots_user_date"),
        {"schema": "finance"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    date: date
    financial_assets: float
    investment_assets: float
    liabilities_credit: float
    liabilities_long_term: float
    net_worth: float
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
