import uuid
from datetime import datetime
from typing import List, Optional, Tuple

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.finance.transaction import Transaction
from app.schemas.finance.transaction import TransactionCreate, TransactionFilter, TransactionUpdate


class TransactionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, data: TransactionCreate) -> Transaction:
        transaction = Transaction(user_id=user_id, **data.model_dump())
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def get_by_id(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Transaction]:
        stmt = select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == user_id
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def list(
        self, user_id: uuid.UUID, filters: TransactionFilter
    ) -> Tuple[List[Transaction], int]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if filters.tag_id:
            stmt = stmt.where(Transaction.tag_id == filters.tag_id)
        if filters.currency:
            stmt = stmt.where(Transaction.currency == filters.currency)
        if filters.date_from:
            stmt = stmt.where(Transaction.date_transaction >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Transaction.date_transaction <= filters.date_to)

        count_stmt = select(sqlalchemy.func.count()).select_from(stmt.subquery())
        total_result = await self.session.exec(count_stmt)
        total = total_result.one()

        stmt = (
            stmt.order_by(Transaction.date_transaction.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        result = await self.session.exec(stmt)
        return list(result.all()), total

    async def update(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID, data: TransactionUpdate
    ) -> Optional[Transaction]:
        transaction = await self.get_by_id(transaction_id, user_id)
        if not transaction:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(transaction, key, value)
        transaction.updated_at = datetime.utcnow()
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def delete(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        transaction = await self.get_by_id(transaction_id, user_id)
        if not transaction:
            return False
        await self.session.delete(transaction)
        await self.session.commit()
        return True
