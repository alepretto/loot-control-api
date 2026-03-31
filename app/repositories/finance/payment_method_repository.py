import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.payment_method import PaymentMethod


class PaymentMethodRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, pm_id: uuid.UUID, user_id: uuid.UUID) -> Optional[PaymentMethod]:
        stmt = select(PaymentMethod).where(
            PaymentMethod.id == pm_id,
            PaymentMethod.user_id == user_id,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_name(self, user_id: uuid.UUID, name: str) -> Optional[PaymentMethod]:
        stmt = select(PaymentMethod).where(
            PaymentMethod.user_id == user_id,
            PaymentMethod.name == name,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[PaymentMethod]:
        stmt = select(PaymentMethod).where(PaymentMethod.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(PaymentMethod.is_active == is_active)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, pm: PaymentMethod) -> PaymentMethod:
        self.session.add(pm)
        await self.session.commit()
        await self.session.refresh(pm)
        return pm

    async def delete(self, pm: PaymentMethod) -> None:
        await self.session.delete(pm)
        await self.session.commit()
