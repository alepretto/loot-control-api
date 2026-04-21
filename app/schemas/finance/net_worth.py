import uuid
from datetime import date, datetime
from typing import List

from pydantic import BaseModel


class NetWorthCurrent(BaseModel):
    financial_assets: float
    investment_assets: float
    liabilities_credit: float
    liabilities_long_term: float
    net_worth: float
    calculated_at: datetime


class NetWorthSnapshotRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    date: date
    financial_assets: float
    investment_assets: float
    liabilities_credit: float
    liabilities_long_term: float
    net_worth: float
    created_at: datetime

    model_config = {"from_attributes": True}


class NetWorthHistory(BaseModel):
    snapshots: List[NetWorthSnapshotRead]
