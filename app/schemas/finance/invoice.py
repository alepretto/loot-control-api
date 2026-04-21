import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.invoice import InvoiceStatus


class InvoiceCreate(BaseModel):
    credit_card_id: uuid.UUID
    reference_month: str  # YYYY-MM
    closing_date: date
    due_date: date
    total_amount: float = 0.0
    status: InvoiceStatus = InvoiceStatus.open


class InvoiceRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    credit_card_id: uuid.UUID
    reference_month: str
    closing_date: date
    due_date: date
    total_amount: float
    status: InvoiceStatus
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceUpdate(BaseModel):
    closing_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[float] = None
    status: Optional[InvoiceStatus] = None


class InvoicePayRequest(BaseModel):
    payment_account_id: uuid.UUID
    payment_date: Optional[datetime] = None