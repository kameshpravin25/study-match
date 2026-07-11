from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    GoogleAuthRequest,
    RegisterComplete,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services.auth_service import authenticate_with_google, create_user_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with Google OAuth. Only Amrita emails allowed."""
    try:
        user, is_new = await authenticate_with_google(request.token, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    token = create_user_token(user)
    return TokenResponse(
        access_token=token,
        is_new_user=is_new,
    )


@router.post("/complete-profile", response_model=UserResponse)
async def complete_profile(
    data: RegisterComplete,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Complete profile after first Google sign-in."""
    if data.department not in settings.departments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid department. Choose from: {settings.departments}",
        )
    if data.campus not in settings.campuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid campus. Choose from: {settings.campuses}",
        )

    user.department = data.department
    user.year = data.year
    user.campus = data.campus
    user.bio = data.bio
    await db.flush()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    update_data = data.model_dump(exclude_unset=True)

    if "department" in update_data and update_data["department"] not in settings.departments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid department",
        )
    if "campus" in update_data and update_data["campus"] not in settings.campuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid campus",
        )

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/config")
async def get_app_config():
    """Get app configuration (departments, campuses, etc.)."""
    return {
        "departments": settings.departments,
        "campuses": settings.campuses,
        "default_campus": settings.default_campus,
    }
