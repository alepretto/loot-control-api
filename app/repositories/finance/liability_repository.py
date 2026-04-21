import uuid
from typing import Optional

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.liability import Liability


class LiabilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, liability_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Liability]:
        stmt = select(Liability).where(Liability.id == liability_id, Liability.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[Liability]:
        stmt = select(Liability).where(Liability.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(Liability.is_active == is_active)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, liability: Liability) -> Liability:
        self.session.add(liability)
        await self.session.commit()
        await self.session.refresh(liability)
        return liability

    async def delete(self, liability: Liability) -> None:
        await self.session.delete(liability)
        await self.session.commit()

    async def get_total_outstanding(self, user_id: uuid.UUID) -> float:
        stmt = select(func.sum(Liability.outstanding_balance)).where(
            Liability.user_id == user_id,
            Liability.is_active == True,
        )
        result = await self.session.exec(stmt)
        total = result.first()
        return float(total) if total else 0.0
