import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.finance.tag_family import TagFamilyCreate, TagFamilyRead, TagFamilyUpdate
from app.services.finance.tag_family_service import TagFamilyService

router = APIRouter(prefix="/finance/tag-families", tags=["tag-families"])


@router.post("/", response_model=TagFamilyRead, status_code=status.HTTP_201_CREATED)
async def create_tag_family(
    data: TagFamilyCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await TagFamilyService(session).create(uuid.UUID(current_user_id), data)


@router.get("/", response_model=List[TagFamilyRead])
async def list_tag_families(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    return await TagFamilyService(session).list(uuid.UUID(current_user_id))


@router.get("/{family_id}", response_model=TagFamilyRead)
async def get_tag_family(
    family_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    family = await TagFamilyService(session).get_by_id(family_id, uuid.UUID(current_user_id))
    if not family:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Família não encontrada")
    return family


@router.patch("/{family_id}", response_model=TagFamilyRead)
async def update_tag_family(
    family_id: uuid.UUID,
    data: TagFamilyUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    family = await TagFamilyService(session).update(
        family_id, uuid.UUID(current_user_id), data
    )
    if not family:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Família não encontrada")
    return family


@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_family(
    family_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
):
    deleted = await TagFamilyService(session).delete(family_id, uuid.UUID(current_user_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Família não encontrada")
