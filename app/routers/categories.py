from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter(tags=["Categories"])


@router.post(
    "/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
def create_category(
    body: CategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        category = category_service.create_category(
            session,
            user_id=current_user.id,
            label=body.label,
            nature=body.nature,
        )
    except ValueError as e:
        msg = str(e)
        if "already exists" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=msg
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return category


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return category_service.list_categories(session, user_id=current_user.id)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        category = category_service.get_category_by_id(session, category_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this category",
        )
    return category


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    body: CategoryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        category = category_service.get_category_by_id(session, category_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this category",
        )

    try:
        return category_service.update_category(
            session,
            category_id=category_id,
            label=body.label,
            nature=body.nature,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        category = category_service.get_category_by_id(session, category_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this category",
        )

    try:
        category_service.delete_category(session, category_id)
    except ValueError as e:
        msg = str(e)
        if "subcategories" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=msg
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
