from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.session import RequestStatus


class JoinRequestCreate(BaseModel):
    message: str | None = Field(None, max_length=500)


class JoinRequestResponse(BaseModel):
    id: UUID
    session_id: UUID
    session_subject: str
    session_scheduled_at: datetime
    requester_id: UUID
    requester_name: str
    requester_department: str
    requester_year: int
    requester_avatar: str | None
    status: RequestStatus
    message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class JoinRequestUpdateRequest(BaseModel):
    status: RequestStatus
