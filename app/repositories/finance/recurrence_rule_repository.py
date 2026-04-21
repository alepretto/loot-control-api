import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.recurrence_rule import RecurrenceRule


class RecurrenceRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> Optional[RecurrenceRule]:
        stmt = select(RecurrenceRule).where(RecurrenceRule.id == rule_id, RecurrenceRule.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[RecurrenceRule]:
        stmt = select(RecurrenceRule).where(RecurrenceRule.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(RecurrenceRule.is_active == is_active)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, rule: RecurrenceRule) -> RecurrenceRule:
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def delete(self, rule: RecurrenceRule) -> None:
        await self.session.delete(rule)
        await self.session.commit()
