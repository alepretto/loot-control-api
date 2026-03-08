import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.tag import TagCreate, TagRead, TagUpdate
from app.services.finance.tag_service import TagService

router = APIRouter(prefix="/finance/tags", tags=["tags"])


@router.post("/", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await TagService(session).create(uuid.UUID(current_user_id), data)


@router.get("/", response_model=List[TagRead])
async def list_tags(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    category_id: Optional[uuid.UUID] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
):
    return await TagService(session).list(
        uuid.UUID(current_user_id), category_id=category_id, is_active=is_active
    )


@router.get("/{tag_id}", response_model=TagRead)
async def get_tag(
    tag_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    tag = await TagService(session).get_by_id(tag_id, uuid.UUID(current_user_id))
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag


@router.patch("/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: uuid.UUID,
    data: TagUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    tag = await TagService(session).update(tag_id, uuid.UUID(current_user_id), data)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await TagService(session).delete(tag_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
