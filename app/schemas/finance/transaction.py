import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.transaction import Currencies
from app.models.finance.tag_family import FamilyNature


class TransactionCreate(BaseModel):
    tag_id: uuid.UUID
    account_id: uuid.UUID
    date_transaction: datetime
    value: float
    currency: Currencies
    description: Optional[str] = None
    invoice_id: Optional[uuid.UUID] = None
    recurrence_id: Optional[uuid.UUID] = None
    is_recurring: bool = False
    quantity: Optional[float] = None
    symbol: Optional[str] = None
    index_rate: Optional[float] = None
    index: Optional[str] = None
    index_percentage: Optional[float] = None


class TransactionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tag_id: uuid.UUID
    account_id: uuid.UUID
    date_transaction: datetime
    value: float
    currency: Currencies
    description: Optional[str]
    invoice_id: Optional[uuid.UUID]
    recurrence_id: Optional[uuid.UUID]
    is_recurring: bool
    quantity: Optional[float]
    symbol: Optional[str]
    index_rate: Optional[float]
    index: Optional[str]
    index_percentage: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionUpdate(BaseModel):
    tag_id: Optional[uuid.UUID] = None
    account_id: Optional[uuid.UUID] = None
    date_transaction: Optional[datetime] = None
    value: Optional[float] = None
    currency: Optional[Currencies] = None
    description: Optional[str] = None
    invoice_id: Optional[uuid.UUID] = None
    credit_card_id: Optional[uuid.UUID] = None  # For assigning to credit card invoice
    recurrence_id: Optional[uuid.UUID] = None
    is_recurring: Optional[bool] = None
    quantity: Optional[float] = None
    symbol: Optional[str] = None
    index_rate: Optional[float] = None
    index: Optional[str] = None
    index_percentage: Optional[float] = None


class TransactionFilter(BaseModel):
    tag_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    family_id: Optional[uuid.UUID] = None
    nature: Optional[FamilyNature] = None
    currency: Optional[Currencies] = None
    account_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
