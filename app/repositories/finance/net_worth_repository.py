import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.net_worth_snapshot import NetWorthSnapshot


class NetWorthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest(self, user_id: uuid.UUID) -> Optional[NetWorthSnapshot]:
        stmt = (
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.date.desc())
            .limit(1)
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_history(self, user_id: uuid.UUID, months: int = 12) -> list[NetWorthSnapshot]:
        stmt = (
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.date.desc())
            .limit(months)
        )
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, snapshot: NetWorthSnapshot) -> NetWorthSnapshot:
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot
