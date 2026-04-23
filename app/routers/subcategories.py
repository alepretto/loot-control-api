from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.subcategory import SubcategoryCreate, SubcategoryResponse, SubcategoryUpdate
from app.services import subcategory_service

router = APIRouter(tags=["Subcategories"])


@router.post(
    "/subcategories", response_model=SubcategoryResponse, status_code=status.HTTP_201_CREATED
)
def create_subcategory(
    body: SubcategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        subcategory = subcategory_service.create_subcategory(
            session,
            user_id=current_user.id,
            label=body.label,
            category_id=body.category_id,
            is_active=body.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return subcategory


@router.get("/subcategories", response_model=list[SubcategoryResponse])
def list_subcategories(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return subcategory_service.list_subcategories(session, user_id=current_user.id)


@router.get("/subcategories/{subcategory_id}", response_model=SubcategoryResponse)
def get_subcategory(
    subcategory_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        subcategory = subcategory_service.get_subcategory_by_id(session, subcategory_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if subcategory.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this subcategory",
        )
    return subcategory


@router.patch("/subcategories/{subcategory_id}", response_model=SubcategoryResponse)
def update_subcategory(
    subcategory_id: UUID,
    body: SubcategoryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        subcategory = subcategory_service.get_subcategory_by_id(session, subcategory_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if subcategory.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this subcategory",
        )

    try:
        return subcategory_service.update_subcategory(
            session,
            subcategory_id=subcategory_id,
            label=body.label,
            category_id=body.category_id,
            is_active=body.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/subcategories/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subcategory(
    subcategory_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        subcategory = subcategory_service.get_subcategory_by_id(session, subcategory_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if subcategory.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this subcategory",
        )

    subcategory_service.delete_subcategory(session, subcategory_id)
