import uuid
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.payment_method import PaymentMethod
from app.repositories.finance.payment_method_repository import PaymentMethodRepository
from app.schemas.finance.payment_method import PaymentMethodCreate, PaymentMethodUpdate


class PaymentMethodService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = PaymentMethodRepository(session)

    async def create(self, user_id: uuid.UUID, data: PaymentMethodCreate) -> PaymentMethod:
        existing = await self.repo.get_by_name(user_id, data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um método de pagamento com este nome",
            )
        pm = PaymentMethod(user_id=user_id, **data.model_dump())
        return await self.repo.save(pm)

    async def get_by_id(self, pm_id: uuid.UUID, user_id: uuid.UUID) -> Optional[PaymentMethod]:
        return await self.repo.get_by_id(pm_id, user_id)

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[PaymentMethod]:
        return await self.repo.list(user_id, is_active=is_active)

    async def update(
        self, pm_id: uuid.UUID, user_id: uuid.UUID, data: PaymentMethodUpdate
    ) -> Optional[PaymentMethod]:
        pm = await self.repo.get_by_id(pm_id, user_id)
        if not pm:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(pm, key, value)
        pm.updated_at = datetime.now(UTC)
        return await self.repo.save(pm)

    async def delete(self, pm_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        pm = await self.repo.get_by_id(pm_id, user_id)
        if not pm:
            return False
        await self.repo.delete(pm)
        return True
