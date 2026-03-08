import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.tag_family import TagFamily


class TagFamilyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_name(self, user_id: uuid.UUID, name: str) -> Optional[TagFamily]:
        stmt = select(TagFamily).where(TagFamily.user_id == user_id, TagFamily.name == name)
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_id(self, family_id: uuid.UUID, user_id: uuid.UUID) -> Optional[TagFamily]:
        stmt = select(TagFamily).where(TagFamily.id == family_id, TagFamily.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def list(self, user_id: uuid.UUID) -> list[TagFamily]:
        stmt = select(TagFamily).where(TagFamily.user_id == user_id)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def save(self, family: TagFamily) -> TagFamily:
        self.session.add(family)
        await self.session.commit()
        await self.session.refresh(family)
        return family

    async def delete(self, family: TagFamily) -> None:
        await self.session.delete(family)
        await self.session.commit()
