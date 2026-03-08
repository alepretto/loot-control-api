import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.finance.category import CategoryType
from app.schemas.finance.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.finance.category_service import CategoryService

router = APIRouter(prefix="/finance/categories", tags=["categories"])


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await CategoryService(session).create(uuid.UUID(current_user_id), data)


@router.get("/", response_model=List[CategoryRead])
async def list_categories(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    type: Optional[CategoryType] = Query(default=None),
):
    return await CategoryService(session).list(uuid.UUID(current_user_id), type=type)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    category = await CategoryService(session).get_by_id(category_id, uuid.UUID(current_user_id))
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    category = await CategoryService(session).update(category_id, uuid.UUID(current_user_id), data)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await CategoryService(session).delete(category_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
