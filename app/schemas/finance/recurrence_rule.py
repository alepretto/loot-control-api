import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models.finance.recurrence_rule import RecurrenceFrequency


class RecurrenceRuleCreate(BaseModel):
    name: str
    frequency: RecurrenceFrequency
    interval: int = 1
    start_date: date
    end_date: Optional[date] = None
    template_transaction: dict[str, Any]
    is_active: bool = True


class RecurrenceRuleRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    frequency: RecurrenceFrequency
    interval: int
    start_date: date
    end_date: Optional[date]
    template_transaction: dict[str, Any]
    is_active: bool
    last_generated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecurrenceRuleUpdate(BaseModel):
    name: Optional[str] = None
    frequency: Optional[RecurrenceFrequency] = None
    interval: Optional[int] = None
    end_date: Optional[date] = None
    template_transaction: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
