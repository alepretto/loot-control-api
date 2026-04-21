from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.budget import Budget
from app.models.finance.category import Category
from app.models.finance.tag import Tag
from app.models.finance.transaction import Transaction
from app.repositories.finance.budget_repository import BudgetRepository
from app.schemas.finance.budget import BudgetCreate, BudgetProgress, BudgetUpdate


class BudgetService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = BudgetRepository(session)
        self.session = session

    async def create(self, user_id: uuid.UUID, data: BudgetCreate) -> Budget:
        if not data.family_id and not data.category_id:
            raise HTTPException(status_code=400, detail="É necessário fornecer family_id ou category_id")
        if data.family_id and data.category_id:
            raise HTTPException(status_code=400, detail="Forneça apenas family_id ou category_id, não ambos")
        budget = Budget(user_id=user_id, **data.model_dump())
        return await self.repo.save(budget)

    async def get_by_id(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Budget]:
        return await self.repo.get_by_id(budget_id, user_id)

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[Budget]:
        return await self.repo.list(user_id, is_active)

    async def update(
        self, budget_id: uuid.UUID, user_id: uuid.UUID, data: BudgetUpdate
    ) -> Optional[Budget]:
        budget = await self.repo.get_by_id(budget_id, user_id)
        if not budget:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(budget, key, value)
        budget.updated_at = datetime.now(UTC)
        return await self.repo.save(budget)

    async def delete(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        budget = await self.repo.get_by_id(budget_id, user_id)
        if not budget:
            return False
        await self.repo.delete(budget)
        return True

    async def get_progress(self, user_id: uuid.UUID, month: str) -> list[BudgetProgress]:
        year, mon = int(month[:4]), int(month[5:7])
        last_day = monthrange(year, mon)[1]
        dt_from = datetime(year, mon, 1, tzinfo=UTC)
        dt_to = datetime(year, mon, last_day, 23, 59, 59, tzinfo=UTC)

        budgets = await self.repo.list(user_id, is_active=True)
        if not budgets:
            return []

        # Otimização: Calcular gastos de todos os budgets em uma única query
        spent_by_budget = await self._calculate_all_spent(user_id, budgets, dt_from, dt_to)

        result = []
        for budget in budgets:
            spent = spent_by_budget.get(budget.id, 0.0)
            remaining = max(0.0, budget.amount - spent)
            usage_pct = round((spent / budget.amount * 100) if budget.amount > 0 else 0.0, 2)
            result.append(BudgetProgress(
                budget_id=budget.id,
                family_id=budget.family_id,
                category_id=budget.category_id,
                amount=budget.amount,
                currency=budget.currency,
                period=budget.period,
                spent=round(spent, 2),
                remaining=round(remaining, 2),
                usage_pct=usage_pct,
            ))
        return result

    async def _calculate_all_spent(
        self, user_id: uuid.UUID, budgets: list[Budget], dt_from: datetime, dt_to: datetime
    ) -> dict[uuid.UUID, float]:
        """Calcula gastos para múltiplos budgets em uma única query."""
        from sqlalchemy import case
        
        # Construir CASE statements para cada budget
        family_ids = [b.family_id for b in budgets if b.family_id]
        category_ids = [b.category_id for b in budgets if b.category_id]
        
        # Query que calcula gastos para todos os budgets de uma vez
        # usando CASE WHEN para separar por family_id ou category_id
        cases = []
        for budget in budgets:
            if budget.family_id:
                cases.append(
                    (Category.family_id == budget.family_id, budget.id)
                )
            elif budget.category_id:
                cases.append(
                    (Tag.category_id == budget.category_id, budget.id)
                )
        
        if not cases:
            return {b.id: 0.0 for b in budgets}
        
        # Query agregada - uma única query para todos os budgets
        stmt = (
            select(
                case(*cases, else_=None).label('budget_id'),
                func.coalesce(func.sum(Transaction.value), 0.0).label('spent')
            )
            .join(Tag, Transaction.tag_id == Tag.id)
            .join(Category, Tag.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.date_transaction >= dt_from,
                Transaction.date_transaction <= dt_to,
            )
            .group_by(case(*cases, else_=None))
            .having(case(*cases, else_=None).isnot(None))
        )
        
        result = await self.session.exec(stmt)
        spent_map = {row[0]: float(row[1]) for row in result.all() if row[0]}
        
        # Garantir que todos os budgets tenham um valor (0.0 se não encontrado)
        return {b.id: spent_map.get(b.id, 0.0) for b in budgets}

    async def _calculate_spent(
        self, user_id: uuid.UUID, budget: Budget, dt_from: datetime, dt_to: datetime
    ) -> float:
        """Método legado - mantido para compatibilidade."""
        stmt = (
            select(func.sum(Transaction.value))
            .join(Tag, Transaction.tag_id == Tag.id)
            .join(Category, Tag.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.date_transaction >= dt_from,
                Transaction.date_transaction <= dt_to,
            )
        )
        if budget.family_id:
            stmt = stmt.where(Category.family_id == budget.family_id)
        elif budget.category_id:
            stmt = stmt.where(Tag.category_id == budget.category_id)

        result = await self.session.exec(stmt)
        total = result.first()
        return float(total) if total else 0.0
