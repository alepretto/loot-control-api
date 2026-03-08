import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def create(self, user_id: uuid.UUID, data: UserCreate) -> User:
        user = User(id=user_id, **data.model_dump())
        return await self.repo.save(user)

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.repo.get_by_id(user_id)

    async def update(self, user_id: uuid.UUID, data: UserUpdate) -> Optional[User]:
        user = await self.repo.get_by_id(user_id)
        if not user:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        user.updated_at = datetime.now(UTC)
        return await self.repo.save(user)
