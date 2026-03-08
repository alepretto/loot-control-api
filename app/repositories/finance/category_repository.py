import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.category import Category, CategoryType


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, category_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Category]:
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def list(
        self,
        user_id: uuid.UUID,
        type: Optional[CategoryType] = None,
    ) -> list[Category]:
        stmt = select(Category).where(Category.user_id == user_id)
        if type is not None:
            stmt = stmt.where(Category.type == type)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, category: Category) -> Category:
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.session.delete(category)
        await self.session.commit()
