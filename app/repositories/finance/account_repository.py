import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.account import Account


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, account_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Account]:
        stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_name(self, user_id: uuid.UUID, name: str) -> Optional[Account]:
        stmt = select(Account).where(Account.user_id == user_id, Account.name == name)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(self, user_id: uuid.UUID, is_active: Optional[bool] = None) -> list[Account]:
        stmt = select(Account).where(Account.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(Account.is_active == is_active)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, account: Account) -> Account:
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def delete(self, account: Account) -> None:
        await self.session.delete(account)
        await self.session.commit()

    async def has_transactions(self, account_id: uuid.UUID) -> bool:
        from app.models.finance.transaction import Transaction
        stmt = select(Transaction).where(Transaction.account_id == account_id).limit(1)
        result = await self.session.exec(stmt)
        return result.first() is not None
