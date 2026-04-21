import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.budget import Budget


class BudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Budget]:
        stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[Budget]:
        stmt = select(Budget).where(Budget.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(Budget.is_active == is_active)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, budget: Budget) -> Budget:
        self.session.add(budget)
        await self.session.commit()
        await self.session.refresh(budget)
        return budget

    async def delete(self, budget: Budget) -> None:
        await self.session.delete(budget)
        await self.session.commit()
