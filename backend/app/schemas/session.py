from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.session import SessionType, SkillLevel, SessionStatus


class SessionCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    topic: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    session_type: SessionType
    location: str | None = Field(None, max_length=255)
    meet_link: str | None = None
    scheduled_at: datetime
    duration_minutes: int = Field(..., ge=15, le=480)
    max_participants: int = Field(5, ge=2, le=50)
    skill_level: SkillLevel = SkillLevel.ANY


class SessionUpdateRequest(BaseModel):
    subject: str | None = Field(None, min_length=1, max_length=255)
    topic: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    session_type: SessionType | None = None
    location: str | None = Field(None, max_length=255)
    meet_link: str | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(None, ge=15, le=480)
    max_participants: int | None = Field(None, ge=2, le=50)
    skill_level: SkillLevel | None = None
    status: SessionStatus | None = None


class ParticipantResponse(BaseModel):
    user_id: UUID
    full_name: str
    department: str
    year: int
    avatar_url: str | None
    joined_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: UUID
    host_id: UUID
    host_name: str
    host_department: str
    host_avatar: str | None
    subject: str
    topic: str | None
    description: str | None
    session_type: SessionType
    location: str | None
    meet_link: str | None
    scheduled_at: datetime
    duration_minutes: int
    max_participants: int
    current_participants: int
    skill_level: SkillLevel
    campus: str
    status: SessionStatus
    created_at: datetime
    has_requested: bool = False
    is_participant: bool = False

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
    page: int
    page_size: int
