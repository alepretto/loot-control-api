import datetime
import uuid

from sqlalchemy import Column, Date
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.finance.transaction import Currencies, currencies_enum


class ExchangeRate(SQLModel, table=True):
    __tablename__ = "exchange_rates"
    __table_args__ = {"schema": "finance"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    currency: Currencies = Field(
        sa_column=Column(currencies_enum, nullable=False)
    )
    rate: float
    date: datetime.date = Field(sa_column=Column("date", Date, index=True))
