import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.payment_method import PaymentMethodType


class PaymentMethodCreate(BaseModel):
    name: str
    type: PaymentMethodType
    account_id: uuid.UUID
    is_active: bool = True


class PaymentMethodRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: PaymentMethodType
    account_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[PaymentMethodType] = None
    is_active: Optional[bool] = None