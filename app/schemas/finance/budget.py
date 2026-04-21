import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.budget import BudgetPeriod
from app.models.finance.transaction import Currencies


class BudgetCreate(BaseModel):
    family_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    amount: float
    currency: Currencies = Currencies.BRL
    period: BudgetPeriod = BudgetPeriod.monthly
    is_active: bool = True


class BudgetRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    family_id: Optional[uuid.UUID]
    category_id: Optional[uuid.UUID]
    amount: float
    currency: Currencies
    period: BudgetPeriod
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetUpdate(BaseModel):
    family_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    amount: Optional[float] = None
    currency: Optional[Currencies] = None
    period: Optional[BudgetPeriod] = None
    is_active: Optional[bool] = None


class BudgetProgress(BaseModel):
    budget_id: uuid.UUID
    family_id: Optional[uuid.UUID]
    category_id: Optional[uuid.UUID]
    amount: float
    currency: Currencies
    period: BudgetPeriod
    spent: float
    remaining: float
    usage_pct: float
