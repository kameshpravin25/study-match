from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.session import RequestStatus
from app.schemas.request import (
    JoinRequestCreate,
    JoinRequestResponse,
    JoinRequestUpdateRequest,
)
from app.services.request_service import (
    create_join_request,
    get_session_requests,
    update_request_status,
    get_user_requests,
)

router = APIRouter(prefix="/requests", tags=["Join Requests"])


@router.post("/sessions/{session_id}/join", response_model=JoinRequestResponse, status_code=201)
async def send_join_request(
    session_id: UUID,
    data: JoinRequestCreate | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a join request to a study session."""
    message = data.message if data else None
    jr = await create_join_request(session_id, user, message, db)

    return JoinRequestResponse(
        id=jr.id,
        session_id=jr.session_id,
        session_subject=jr.session.subject,
        session_scheduled_at=jr.session.scheduled_at,
        requester_id=jr.requester_id,
        requester_name=user.full_name,
        requester_department=user.department,
        requester_year=user.year,
        requester_avatar=user.avatar_url,
        status=jr.status,
        message=jr.message,
        created_at=jr.created_at,
    )


@router.get("/sessions/{session_id}", response_model=list[JoinRequestResponse])
async def list_session_requests(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View join requests for a session (host only)."""
    return await get_session_requests(session_id, user, db)


@router.put("/{request_id}", response_model=JoinRequestResponse)
async def manage_request(
    request_id: UUID,
    data: JoinRequestUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept or reject a join request (host only)."""
    jr = await update_request_status(request_id, data.status, user, db)

    return JoinRequestResponse(
        id=jr.id,
        session_id=jr.session_id,
        session_subject=jr.session.subject,
        session_scheduled_at=jr.session.scheduled_at,
        requester_id=jr.requester_id,
        requester_name=jr.requester.full_name,
        requester_department=jr.requester.department,
        requester_year=jr.requester.year,
        requester_avatar=jr.requester.avatar_url,
        status=jr.status,
        message=jr.message,
        created_at=jr.created_at,
    )


@router.get("/mine/sent", response_model=list[JoinRequestResponse])
async def my_sent_requests(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get join requests I've sent."""
    return await get_user_requests(user, db, "sent")


@router.get("/mine/received", response_model=list[JoinRequestResponse])
async def my_received_requests(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get join requests for my sessions."""
    return await get_user_requests(user, db, "received")
