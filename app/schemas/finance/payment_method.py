import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.payment_method import PaymentMethodCategory


class PaymentMethodCreate(BaseModel):
    name: str
    category: PaymentMethodCategory
    is_active: bool = True


class PaymentMethodRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    category: PaymentMethodCategory
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[PaymentMethodCategory] = None
    is_active: Optional[bool] = None
