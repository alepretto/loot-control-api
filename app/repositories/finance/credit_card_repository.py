import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.credit_card import CreditCard


class CreditCardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, card: CreditCard) -> CreditCard:
        self.session.add(card)
        await self.session.commit()
        await self.session.refresh(card)
        return card

    async def get_by_id(self, card_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CreditCard]:
        stmt = select(CreditCard).where(
            CreditCard.id == card_id,
            CreditCard.user_id == user_id,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_payment_method(self, pm_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CreditCard]:
        stmt = select(CreditCard).where(
            CreditCard.payment_method_id == pm_id,
            CreditCard.user_id == user_id,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[CreditCard]:
        stmt = select(CreditCard).where(CreditCard.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(CreditCard.is_active == is_active)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def delete(self, card: CreditCard) -> None:
        await self.session.delete(card)
        await self.session.commit()