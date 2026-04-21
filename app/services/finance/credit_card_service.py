import uuid
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.credit_card import CreditCard
from app.repositories.finance.credit_card_repository import CreditCardRepository
from app.schemas.finance.credit_card import CreditCardCreate, CreditCardUpdate


class CreditCardService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CreditCardRepository(session)
        self.session = session

    async def create(self, user_id: uuid.UUID, data: CreditCardCreate) -> CreditCard:
        existing = await self.repo.get_by_payment_method(data.payment_method_id, user_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Cartão já existe para este método de pagamento",
            )
        card = CreditCard(user_id=user_id, **data.model_dump())
        return await self.repo.save(card)

    async def get_by_id(self, card_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CreditCard]:
        return await self.repo.get_by_id(card_id, user_id)

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[CreditCard]:
        return await self.repo.list(user_id, is_active)

    async def update(
        self, card_id: uuid.UUID, user_id: uuid.UUID, data: CreditCardUpdate
    ) -> Optional[CreditCard]:
        card = await self.repo.get_by_id(card_id, user_id)
        if not card:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(card, key, value)
        card.updated_at = datetime.now(UTC)
        return await self.repo.save(card)

    async def delete(self, card_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        card = await self.repo.get_by_id(card_id, user_id)
        if not card:
            return False
        await self.repo.delete(card)
        return True