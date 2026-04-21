from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreditCardCreate(BaseModel):
    payment_method_id: UUID
    name: str
    limit_amount: float
    due_day: int = Field(ge=1, le=31)
    closing_offset: int = Field(default=3, ge=1, le=10)


class CreditCardUpdate(BaseModel):
    name: Optional[str] = None
    limit_amount: Optional[float] = None
    due_day: Optional[int] = Field(default=None, ge=1, le=31)
    closing_offset: Optional[int] = Field(default=None, ge=1, le=10)
    is_active: Optional[bool] = None


class CreditCardRead(BaseModel):
    id: UUID
    payment_method_id: UUID
    user_id: UUID
    name: str
    limit_amount: float
    due_day: int
    closing_offset: int
    current_balance: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    closing_day: int

    class Config:
        from_attributes = True