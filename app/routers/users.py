import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    """Called after Supabase signup to sync user profile."""
    user = User(id=uuid.UUID(current_user_id), **data.model_dump())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
async def get_me(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    stmt = select(User).where(User.id == uuid.UUID(current_user_id))
    result = await session.exec(stmt)
    user = result.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    stmt = select(User).where(User.id == uuid.UUID(current_user_id))
    result = await session.exec(stmt)
    user = result.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user
