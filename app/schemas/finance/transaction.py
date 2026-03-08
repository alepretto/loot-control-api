import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.transaction import Currencies


class TransactionCreate(BaseModel):
    tag_id: uuid.UUID
    date_transaction: datetime
    value: float
    currency: Currencies
    quantity: Optional[float] = None
    symbol: Optional[str] = None
    index_rate: Optional[float] = None
    index: Optional[str] = None


class TransactionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tag_id: uuid.UUID
    date_transaction: datetime
    value: float
    currency: Currencies
    quantity: Optional[float]
    symbol: Optional[str]
    index_rate: Optional[float]
    index: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionUpdate(BaseModel):
    tag_id: Optional[uuid.UUID] = None
    date_transaction: Optional[datetime] = None
    value: Optional[float] = None
    currency: Optional[Currencies] = None
    quantity: Optional[float] = None
    symbol: Optional[str] = None
    index_rate: Optional[float] = None
    index: Optional[str] = None


class TransactionFilter(BaseModel):
    tag_id: Optional[uuid.UUID] = None
    currency: Optional[Currencies] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
