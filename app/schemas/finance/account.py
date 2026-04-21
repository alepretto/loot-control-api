import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finance.account import AccountType, BalanceMode
from app.models.finance.transaction import Currencies


class AccountCreate(BaseModel):
    name: str
    type: AccountType
    institution: Optional[str] = None
    currency: Currencies = Currencies.BRL
    balance_mode: BalanceMode = BalanceMode.calculated
    manual_balance: Optional[float] = None
    credit_limit: Optional[float] = None
    closing_day: Optional[int] = None
    due_day: Optional[int] = None
    is_active: bool = True


class AccountRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: AccountType
    institution: Optional[str]
    currency: Currencies
    balance_mode: BalanceMode
    manual_balance: Optional[float]
    credit_limit: Optional[float]
    closing_day: Optional[int]
    due_day: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountReadWithBalance(AccountRead):
    balance: Optional[float] = None
    # For wallet/broker accounts: shows quantity per symbol for debugging
    holdings: Optional[dict[str, float]] = None
    # URL to fetch account statement (transactions)
    statement_url: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[AccountType] = None
    institution: Optional[str] = None
    currency: Optional[Currencies] = None
    balance_mode: Optional[BalanceMode] = None
    manual_balance: Optional[float] = None
    credit_limit: Optional[float] = None
    closing_day: Optional[int] = None
    due_day: Optional[int] = None
    is_active: Optional[bool] = None