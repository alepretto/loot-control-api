from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.recurrence_rule import RecurrenceRule
from app.repositories.finance.recurrence_rule_repository import RecurrenceRuleRepository
from app.schemas.finance.recurrence_rule import RecurrenceRuleCreate, RecurrenceRuleUpdate


class RecurrenceRuleService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = RecurrenceRuleRepository(session)

    async def create(self, user_id: uuid.UUID, data: RecurrenceRuleCreate) -> RecurrenceRule:
        rule = RecurrenceRule(user_id=user_id, **data.model_dump())
        return await self.repo.save(rule)

    async def get_by_id(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> Optional[RecurrenceRule]:
        return await self.repo.get_by_id(rule_id, user_id)

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[RecurrenceRule]:
        return await self.repo.list(user_id, is_active)

    async def update(
        self, rule_id: uuid.UUID, user_id: uuid.UUID, data: RecurrenceRuleUpdate
    ) -> Optional[RecurrenceRule]:
        rule = await self.repo.get_by_id(rule_id, user_id)
        if not rule:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)
        rule.updated_at = datetime.now(UTC)
        return await self.repo.save(rule)

    async def delete(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        rule = await self.repo.get_by_id(rule_id, user_id)
        if not rule:
            return False
        await self.repo.delete(rule)
        return True
