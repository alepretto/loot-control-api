from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.liability import Liability
from app.repositories.finance.liability_repository import LiabilityRepository
from app.schemas.finance.liability import LiabilityCreate, LiabilityUpdate


class LiabilityService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = LiabilityRepository(session)

    async def create(self, user_id: uuid.UUID, data: LiabilityCreate) -> Liability:
        liability = Liability(user_id=user_id, **data.model_dump())
        return await self.repo.save(liability)

    async def get_by_id(self, liability_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Liability]:
        return await self.repo.get_by_id(liability_id, user_id)

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[Liability]:
        return await self.repo.list(user_id, is_active)

    async def update(
        self, liability_id: uuid.UUID, user_id: uuid.UUID, data: LiabilityUpdate
    ) -> Optional[Liability]:
        liability = await self.repo.get_by_id(liability_id, user_id)
        if not liability:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(liability, key, value)
        liability.updated_at = datetime.now(UTC)
        return await self.repo.save(liability)

    async def delete(self, liability_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        liability = await self.repo.get_by_id(liability_id, user_id)
        if not liability:
            return False
        await self.repo.delete(liability)
        return True
