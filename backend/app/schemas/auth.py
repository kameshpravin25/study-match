from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class GoogleAuthRequest(BaseModel):
    token: str = Field(..., description="Google OAuth ID token")


class RegisterComplete(BaseModel):
    department: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=1, le=5)
    campus: str = Field(..., min_length=1, max_length=50)
    bio: str | None = Field(None, max_length=500)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    avatar_url: str | None
    department: str
    year: int
    campus: str
    bio: str | None
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    department: str | None = Field(None, min_length=1, max_length=50)
    year: int | None = Field(None, ge=1, le=5)
    campus: str | None = Field(None, min_length=1, max_length=50)
    bio: str | None = Field(None, max_length=500)
