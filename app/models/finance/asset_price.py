import datetime
import uuid

from sqlalchemy import Column, Date
from sqlmodel import Field, SQLModel

from app.models.finance.transaction import Currencies, currencies_enum


class AssetPrice(SQLModel, table=True):
    __tablename__ = "asset_prices"
    __table_args__ = {"schema": "finance"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    symbol: str = Field(index=True)
    price: float
    currency: Currencies = Field(
        sa_column=Column(currencies_enum, nullable=False)
    )
    date: datetime.date = Field(sa_column=Column("date", Date, index=True))
