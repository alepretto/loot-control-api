import uuid
from typing import Optional

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.category import Category
from app.models.finance.tag import Tag
from app.models.finance.transaction import Currencies, Transaction


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Transaction]:
        stmt = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def list(
        self,
        user_id: uuid.UUID,
        tag_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        family_id: Optional[uuid.UUID] = None,
        currency: Optional[Currencies] = None,
        date_from: Optional[object] = None,
        date_to: Optional[object] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Transaction], int]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if tag_id is not None:
            stmt = stmt.where(Transaction.tag_id == tag_id)
        if category_id is not None:
            stmt = stmt.join(Tag, Transaction.tag_id == Tag.id).where(
                Tag.category_id == category_id
            )
        if family_id is not None:
            if category_id is None:
                stmt = stmt.join(Tag, Transaction.tag_id == Tag.id)
            stmt = stmt.join(Category, Tag.category_id == Category.id).where(
                Category.family_id == family_id
            )
        if currency is not None:
            stmt = stmt.where(Transaction.currency == currency)
        if date_from is not None:
            stmt = stmt.where(Transaction.date_transaction >= date_from)
        if date_to is not None:
            stmt = stmt.where(Transaction.date_transaction <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.exec(count_stmt)).one()

        items = (
            await self.session.exec(
                stmt.order_by(Transaction.date_transaction.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()

        return list(items), total

    async def save(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def delete(self, transaction: Transaction) -> None:
        await self.session.delete(transaction)
        await self.session.commit()
