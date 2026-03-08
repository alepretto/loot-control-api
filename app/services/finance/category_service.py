import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.category import Category, CategoryType
from app.repositories.finance.category_repository import CategoryRepository
from app.schemas.finance.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CategoryRepository(session)

    async def create(self, user_id: uuid.UUID, data: CategoryCreate) -> Category:
        category = Category(user_id=user_id, **data.model_dump())
        return await self.repo.save(category)

    async def get_by_id(
        self, category_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Category]:
        return await self.repo.get_by_id(category_id, user_id)

    async def list(
        self,
        user_id: uuid.UUID,
        type: Optional[CategoryType] = None,
    ) -> list[Category]:
        return await self.repo.list(user_id, type=type)

    async def update(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CategoryUpdate,
    ) -> Optional[Category]:
        category = await self.repo.get_by_id(category_id, user_id)
        if not category:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        category.updated_at = datetime.now(UTC)
        return await self.repo.save(category)

    async def delete(self, category_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        category = await self.repo.get_by_id(category_id, user_id)
        if not category:
            return False
        await self.repo.delete(category)
        return True
