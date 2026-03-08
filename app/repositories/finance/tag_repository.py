import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.category import CategoryType
from app.models.finance.tag import Tag


class TagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Tag]:
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(
        self,
        user_id: uuid.UUID,
        category_id: Optional[uuid.UUID] = None,
        type: Optional[CategoryType] = None,
        is_active: Optional[bool] = None,
    ) -> list[Tag]:
        stmt = select(Tag).where(Tag.user_id == user_id)
        if category_id is not None:
            stmt = stmt.where(Tag.category_id == category_id)
        if type is not None:
            stmt = stmt.where(Tag.type == type)
        if is_active is not None:
            stmt = stmt.where(Tag.is_active == is_active)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def get_by_name_and_category(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        name: str,
    ) -> Optional[Tag]:
        stmt = select(Tag).where(
            Tag.user_id == user_id,
            Tag.category_id == category_id,
            Tag.name == name,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def save(self, tag: Tag) -> Tag:
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def delete(self, tag: Tag) -> None:
        await self.session.delete(tag)
        await self.session.commit()
