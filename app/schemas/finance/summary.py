from typing import Optional

from pydantic import BaseModel


class MonthlySummaryResponse(BaseModel):
    month: int
    year: int
    total_income: float
    total_fixed_expense: float
    total_variable_expense: float
    total_investment: float
    total_expense: float
    balance: float
    saving_rate: float
    income_by_type: dict[str, float]
    by_family: dict[str, dict[str, float]]
    top_tags: list[dict[str, float]]
    has_foreign_currency: bool