from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserPreferencesUpdate,
    UserResponse,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(tags=["Users"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, session: Session = Depends(get_session)):
    try:
        user = user_service.signup(
            session,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            password=body.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    try:
        token = user_service.login(session, email=body.email, password=body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(access_token=token)


@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/users/me/preferences", response_model=UserResponse)
def update_my_preferences(
    body: UserPreferencesUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_preferences(
        session, current_user, display_currency_id=body.display_currency_id
    )


@router.get("/users", response_model=list[UserResponse])
def read_users(
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    return user_service.list_users(session)


@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    try:
        return user_service.get_user_by_id(session, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))