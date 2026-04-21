import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.liability import LiabilityIndex, LiabilityType


class LiabilityCreate(BaseModel):
    name: str
    type: LiabilityType
    institution: Optional[str] = None
    total_value: float
    outstanding_balance: float
    monthly_payment: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    interest_rate: Optional[float] = None
    index: Optional[LiabilityIndex] = None
    is_active: bool = True


class LiabilityRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: LiabilityType
    institution: Optional[str]
    total_value: float
    outstanding_balance: float
    monthly_payment: Optional[float]
    start_date: Optional[date]
    end_date: Optional[date]
    interest_rate: Optional[float]
    index: Optional[LiabilityIndex]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LiabilityUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[LiabilityType] = None
    institution: Optional[str] = None
    total_value: Optional[float] = None
    outstanding_balance: Optional[float] = None
    monthly_payment: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    interest_rate: Optional[float] = None
    index: Optional[LiabilityIndex] = None
    is_active: Optional[bool] = None
