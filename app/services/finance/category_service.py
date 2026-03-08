import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.finance.category import Category, CategoryType
from app.schemas.finance.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, data: CategoryCreate) -> Category:
        category = Category(user_id=user_id, **data.model_dump())
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def get_by_id(self, category_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Category]:
        stmt = select(Category).where(Category.id == category_id, Category.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(
        self,
        user_id: uuid.UUID,
        type: Optional[CategoryType] = None,
    ) -> List[Category]:
        stmt = select(Category).where(Category.user_id == user_id)
        if type:
            stmt = stmt.where(Category.type == type)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def update(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CategoryUpdate,
    ) -> Optional[Category]:
        category = await self.get_by_id(category_id, user_id)
        if not category:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        category.updated_at = datetime.utcnow()
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        category = await self.get_by_id(category_id, user_id)
        if not category:
            return False
        await self.session.delete(category)
        await self.session.commit()
        return True
