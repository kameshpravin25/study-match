import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status

from app.models.session import (
    StudySession,
    SessionParticipant,
    JoinRequest,
    SessionStatus,
    RequestStatus,
)
from app.models.user import User
from app.schemas.session import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
)


async def create_session(
    data: SessionCreateRequest,
    user: User,
    db: AsyncSession,
) -> StudySession:
    session = StudySession(
        host_id=user.id,
        subject=data.subject,
        topic=data.topic,
        description=data.description,
        session_type=data.session_type,
        location=data.location,
        meet_link=data.meet_link,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        max_participants=data.max_participants,
        skill_level=data.skill_level,
        campus=user.campus,
        status=SessionStatus.OPEN,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_sessions(
    db: AsyncSession,
    campus: str | None = None,
    subject: str | None = None,
    session_type: str | None = None,
    skill_level: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user_id: uuid.UUID | None = None,
) -> tuple[list[dict], int]:
    query = (
        select(StudySession)
        .where(StudySession.status == SessionStatus.OPEN)
        .where(StudySession.scheduled_at >= datetime.now(timezone.utc))
        .order_by(StudySession.scheduled_at.asc())
    )

    if campus:
        query = query.where(StudySession.campus == campus)
    if subject:
        query = query.where(StudySession.subject.ilike(f"%{subject}%"))
    if session_type:
        query = query.where(StudySession.session_type == session_type)
    if skill_level:
        query = query.where(StudySession.skill_level == skill_level)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    # Build response with participant counts
    session_responses = []
    for s in sessions:
        participant_count = len(s.participants)
        has_requested = False
        is_participant = False

        if current_user_id:
            has_requested = any(
                jr.requester_id == current_user_id
                for jr in s.join_requests
            )
            is_participant = any(
                p.user_id == current_user_id for p in s.participants
            )

        session_responses.append(
            SessionResponse(
                id=s.id,
                host_id=s.host_id,
                host_name=s.host.full_name,
                host_department=s.host.department,
                host_avatar=s.host.avatar_url,
                subject=s.subject,
                topic=s.topic,
                description=s.description,
                session_type=s.session_type,
                location=s.location,
                meet_link=s.meet_link,
                scheduled_at=s.scheduled_at,
                duration_minutes=s.duration_minutes,
                max_participants=s.max_participants,
                current_participants=participant_count,
                skill_level=s.skill_level,
                campus=s.campus,
                status=s.status,
                created_at=s.created_at,
                has_requested=has_requested,
                is_participant=is_participant,
            )
        )

    return session_responses, total


async def get_session_by_id(
    session_id: uuid.UUID,
    db: AsyncSession,
    current_user_id: uuid.UUID | None = None,
) -> SessionResponse:
    result = await db.execute(
        select(StudySession).where(StudySession.id == session_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    participant_count = len(s.participants)
    has_requested = False
    is_participant = False

    if current_user_id:
        has_requested = any(
            jr.requester_id == current_user_id for jr in s.join_requests
        )
        is_participant = any(
            p.user_id == current_user_id for p in s.participants
        )

    return SessionResponse(
        id=s.id,
        host_id=s.host_id,
        host_name=s.host.full_name,
        host_department=s.host.department,
        host_avatar=s.host.avatar_url,
        subject=s.subject,
        topic=s.topic,
        description=s.description,
        session_type=s.session_type,
        location=s.location,
        meet_link=s.meet_link,
        scheduled_at=s.scheduled_at,
        duration_minutes=s.duration_minutes,
        max_participants=s.max_participants,
        current_participants=participant_count,
        skill_level=s.skill_level,
        campus=s.campus,
        status=s.status,
        created_at=s.created_at,
        has_requested=has_requested,
        is_participant=is_participant,
    )


async def update_session(
    session_id: uuid.UUID,
    data: SessionUpdateRequest,
    user: User,
    db: AsyncSession,
) -> StudySession:
    result = await db.execute(
        select(StudySession).where(StudySession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.host_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can update this session",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)

    await db.flush()
    await db.refresh(session)
    return session


async def delete_session(
    session_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(StudySession).where(StudySession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.host_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can cancel this session",
        )

    session.status = SessionStatus.CANCELLED
    await db.flush()


async def get_user_sessions(
    user: User,
    db: AsyncSession,
    role: str = "all",
) -> list[SessionResponse]:
    """Get sessions where user is host or participant."""
    sessions = []

    if role in ("all", "hosting"):
        result = await db.execute(
            select(StudySession)
            .where(StudySession.host_id == user.id)
            .where(StudySession.status != SessionStatus.CANCELLED)
            .order_by(StudySession.scheduled_at.desc())
        )
        for s in result.scalars().all():
            sessions.append(
                SessionResponse(
                    id=s.id,
                    host_id=s.host_id,
                    host_name=s.host.full_name,
                    host_department=s.host.department,
                    host_avatar=s.host.avatar_url,
                    subject=s.subject,
                    topic=s.topic,
                    description=s.description,
                    session_type=s.session_type,
                    location=s.location,
                    meet_link=s.meet_link,
                    scheduled_at=s.scheduled_at,
                    duration_minutes=s.duration_minutes,
                    max_participants=s.max_participants,
                    current_participants=len(s.participants),
                    skill_level=s.skill_level,
                    campus=s.campus,
                    status=s.status,
                    created_at=s.created_at,
                    has_requested=False,
                    is_participant=True,
                )
            )

    if role in ("all", "joined"):
        result = await db.execute(
            select(StudySession)
            .join(SessionParticipant)
            .where(SessionParticipant.user_id == user.id)
            .where(StudySession.host_id != user.id)
            .where(StudySession.status != SessionStatus.CANCELLED)
            .order_by(StudySession.scheduled_at.desc())
        )
        for s in result.scalars().all():
            sessions.append(
                SessionResponse(
                    id=s.id,
                    host_id=s.host_id,
                    host_name=s.host.full_name,
                    host_department=s.host.department,
                    host_avatar=s.host.avatar_url,
                    subject=s.subject,
                    topic=s.topic,
                    description=s.description,
                    session_type=s.session_type,
                    location=s.location,
                    meet_link=s.meet_link,
                    scheduled_at=s.scheduled_at,
                    duration_minutes=s.duration_minutes,
                    max_participants=s.max_participants,
                    current_participants=len(s.participants),
                    skill_level=s.skill_level,
                    campus=s.campus,
                    status=s.status,
                    created_at=s.created_at,
                    has_requested=False,
                    is_participant=True,
                )
            )

    return sessions
