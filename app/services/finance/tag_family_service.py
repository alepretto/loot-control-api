import uuid
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.finance.tag_family import TagFamily
from app.repositories.finance.tag_family_repository import TagFamilyRepository
from app.schemas.finance.tag_family import TagFamilyCreate, TagFamilyUpdate


class TagFamilyService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TagFamilyRepository(session)

    async def create(self, user_id: uuid.UUID, data: TagFamilyCreate) -> TagFamily:
        existing = await self.repo.get_by_name(user_id, data.name)
        if existing:
            raise HTTPException(status_code=409, detail="Família com esse nome já existe")
        family = TagFamily(user_id=user_id, **data.model_dump())
        return await self.repo.save(family)

    async def get_by_id(self, family_id: uuid.UUID, user_id: uuid.UUID) -> Optional[TagFamily]:
        return await self.repo.get_by_id(family_id, user_id)

    async def list(self, user_id: uuid.UUID) -> list[TagFamily]:
        return await self.repo.list(user_id)

    async def update(
        self,
        family_id: uuid.UUID,
        user_id: uuid.UUID,
        data: TagFamilyUpdate,
    ) -> Optional[TagFamily]:
        family = await self.repo.get_by_id(family_id, user_id)
        if not family:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(family, key, value)
        family.updated_at = datetime.now(UTC)
        return await self.repo.save(family)

    async def delete(self, family_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        family = await self.repo.get_by_id(family_id, user_id)
        if not family:
            return False
        await self.repo.delete(family)
        return True
