import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.transaction import Transaction
from app.repositories.finance.transaction_repository import TransactionRepository
from app.schemas.finance.transaction import TransactionCreate, TransactionFilter, TransactionUpdate


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TransactionRepository(session)

    async def create(self, user_id: uuid.UUID, data: TransactionCreate) -> Transaction:
        transaction = Transaction(user_id=user_id, **data.model_dump())
        return await self.repo.save(transaction)

    async def get_by_id(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Transaction]:
        return await self.repo.get_by_id(transaction_id, user_id)

    async def list(
        self, user_id: uuid.UUID, filters: TransactionFilter
    ) -> tuple[list[Transaction], int]:
        return await self.repo.list(
            user_id,
            tag_id=filters.tag_id,
            currency=filters.currency,
            date_from=filters.date_from,
            date_to=filters.date_to,
            page=filters.page,
            page_size=filters.page_size,
        )

    async def update(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID, data: TransactionUpdate
    ) -> Optional[Transaction]:
        transaction = await self.repo.get_by_id(transaction_id, user_id)
        if not transaction:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(transaction, key, value)
        transaction.updated_at = datetime.now(UTC)
        return await self.repo.save(transaction)

    async def delete(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        transaction = await self.repo.get_by_id(transaction_id, user_id)
        if not transaction:
            return False
        await self.repo.delete(transaction)
        return True
