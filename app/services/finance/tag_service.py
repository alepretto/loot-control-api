import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.finance.tag import Tag
from app.schemas.finance.tag import TagCreate, TagUpdate


class TagService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, data: TagCreate) -> Tag:
        tag = Tag(user_id=user_id, **data.model_dump())
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def get_by_id(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Tag]:
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(
        self,
        user_id: uuid.UUID,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> List[Tag]:
        stmt = select(Tag).where(Tag.user_id == user_id)
        if category_id:
            stmt = stmt.where(Tag.category_id == category_id)
        if is_active is not None:
            stmt = stmt.where(Tag.is_active == is_active)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def update(self, tag_id: uuid.UUID, user_id: uuid.UUID, data: TagUpdate) -> Optional[Tag]:
        tag = await self.get_by_id(tag_id, user_id)
        if not tag:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(tag, key, value)
        tag.updated_at = datetime.utcnow()
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def delete(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        tag = await self.get_by_id(tag_id, user_id)
        if not tag:
            return False
        await self.session.delete(tag)
        await self.session.commit()
        return True
