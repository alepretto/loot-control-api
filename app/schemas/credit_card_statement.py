from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# --- Request schemas ---


class CreditCardStatementCreate(BaseModel):
    credit_card_id: UUID
    end_date: datetime
    is_paid: bool = False
    total_amount: float | None = None


class CreditCardStatementUpdate(BaseModel):
    end_date: datetime | None = None
    is_paid: bool | None = None
    total_amount: float | None = None


# --- Response schemas ---


class CreditCardStatementResponse(BaseModel):
    id: UUID
    user_id: UUID
    credit_card_id: UUID
    end_date: datetime
    is_paid: bool
    total_amount: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
