import uuid
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.category import CategoryType
from app.models.finance.tag import Tag
from app.repositories.finance.tag_repository import TagRepository
from app.schemas.finance.tag import TagCreate, TagUpdate


class TagService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TagRepository(session)

    async def create(self, user_id: uuid.UUID, data: TagCreate) -> Tag:
        existing = await self.repo.get_by_name_and_category(user_id, data.category_id, data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma tag com este nome nesta categoria",
            )
        tag = Tag(user_id=user_id, **data.model_dump())
        return await self.repo.save(tag)

    async def get_by_id(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Tag]:
        return await self.repo.get_by_id(tag_id, user_id)

    async def list(
        self,
        user_id: uuid.UUID,
        category_id: Optional[uuid.UUID] = None,
        type: Optional[CategoryType] = None,
        is_active: Optional[bool] = None,
    ) -> list[Tag]:
        return await self.repo.list(user_id, category_id=category_id, type=type, is_active=is_active)

    async def update(
        self, tag_id: uuid.UUID, user_id: uuid.UUID, data: TagUpdate
    ) -> Optional[Tag]:
        tag = await self.repo.get_by_id(tag_id, user_id)
        if not tag:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(tag, key, value)
        tag.updated_at = datetime.now(UTC)
        return await self.repo.save(tag)

    async def delete(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        tag = await self.repo.get_by_id(tag_id, user_id)
        if not tag:
            return False
        await self.repo.delete(tag)
        return True
