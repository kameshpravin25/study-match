from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.session import SessionType, SkillLevel
from app.schemas.session import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse,
)
from app.services.session_service import (
    create_session,
    get_sessions,
    get_session_by_id,
    update_session,
    delete_session,
    get_user_sessions,
)

router = APIRouter(prefix="/sessions", tags=["Study Sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_study_session(
    data: SessionCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new study session."""
    session = await create_session(data, user, db)
    return SessionResponse(
        id=session.id,
        host_id=session.host_id,
        host_name=user.full_name,
        host_department=user.department,
        host_avatar=user.avatar_url,
        subject=session.subject,
        topic=session.topic,
        description=session.description,
        session_type=session.session_type,
        location=session.location,
        meet_link=session.meet_link,
        scheduled_at=session.scheduled_at,
        duration_minutes=session.duration_minutes,
        max_participants=session.max_participants,
        current_participants=0,
        skill_level=session.skill_level,
        campus=session.campus,
        status=session.status,
        created_at=session.created_at,
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    campus: str | None = Query(None),
    subject: str | None = Query(None),
    session_type: str | None = Query(None),
    skill_level: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Browse upcoming study sessions with filters."""
    sessions, total = await get_sessions(
        db=db,
        campus=campus,
        subject=subject,
        session_type=session_type,
        skill_level=skill_level,
        page=page,
        page_size=page_size,
        current_user_id=user.id,
    )
    return SessionListResponse(
        sessions=sessions,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/mine")
async def my_sessions(
    role: str = Query("all", regex="^(all|hosting|joined)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get my hosted and joined sessions."""
    return await get_user_sessions(user, db, role)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get session details."""
    return await get_session_by_id(session_id, db, user.id)


@router.put("/{session_id}", response_model=SessionResponse)
async def update_study_session(
    session_id: UUID,
    data: SessionUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a session (host only)."""
    session = await update_session(session_id, data, user, db)
    return await get_session_by_id(session_id, db, user.id)


@router.delete("/{session_id}", status_code=204)
async def cancel_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a session (host only)."""
    await delete_session(session_id, user, db)
