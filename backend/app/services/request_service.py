import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.session import (
    JoinRequest,
    StudySession,
    SessionParticipant,
    RequestStatus,
    SessionStatus,
)
from app.models.user import User
from app.schemas.request import JoinRequestResponse


async def create_join_request(
    session_id: uuid.UUID,
    user: User,
    message: str | None,
    db: AsyncSession,
) -> JoinRequest:
    # Check session exists and is open
    result = await db.execute(
        select(StudySession).where(StudySession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.status != SessionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not open for requests",
        )
    if session.host_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot join your own session",
        )

    # Check if already requested
    existing = await db.execute(
        select(JoinRequest).where(
            and_(
                JoinRequest.session_id == session_id,
                JoinRequest.requester_id == user.id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already requested to join this session",
        )

    # Check if already participant
    existing_p = await db.execute(
        select(SessionParticipant).where(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == user.id,
            )
        )
    )
    if existing_p.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a participant",
        )

    # Check capacity
    participant_count = len(session.participants)
    if participant_count >= session.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is full",
        )

    join_request = JoinRequest(
        session_id=session_id,
        requester_id=user.id,
        message=message,
        status=RequestStatus.PENDING,
    )
    db.add(join_request)
    await db.flush()
    await db.refresh(join_request)
    return join_request


async def get_session_requests(
    session_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> list[JoinRequestResponse]:
    # Verify user is host
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
            detail="Only the host can view requests",
        )

    result = await db.execute(
        select(JoinRequest)
        .where(JoinRequest.session_id == session_id)
        .order_by(JoinRequest.created_at.desc())
    )
    requests = result.scalars().all()

    return [
        JoinRequestResponse(
            id=r.id,
            session_id=r.session_id,
            session_subject=session.subject,
            session_scheduled_at=session.scheduled_at,
            requester_id=r.requester_id,
            requester_name=r.requester.full_name,
            requester_department=r.requester.department,
            requester_year=r.requester.year,
            requester_avatar=r.requester.avatar_url,
            status=r.status,
            message=r.message,
            created_at=r.created_at,
        )
        for r in requests
    ]


async def update_request_status(
    request_id: uuid.UUID,
    new_status: RequestStatus,
    user: User,
    db: AsyncSession,
) -> JoinRequest:
    result = await db.execute(
        select(JoinRequest).where(JoinRequest.id == request_id)
    )
    join_request = result.scalar_one_or_none()
    if not join_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    # Verify the user is the session host
    result = await db.execute(
        select(StudySession).where(StudySession.id == join_request.session_id)
    )
    session = result.scalar_one_or_none()
    if session.host_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can manage requests",
        )

    if join_request.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request already {join_request.status.value}",
        )

    join_request.status = new_status

    # If accepted, add as participant
    if new_status == RequestStatus.ACCEPTED:
        participant_count = len(session.participants)
        if participant_count >= session.max_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is full",
            )

        participant = SessionParticipant(
            session_id=join_request.session_id,
            user_id=join_request.requester_id,
        )
        db.add(participant)

        # Check if session is now full
        if participant_count + 1 >= session.max_participants:
            session.status = SessionStatus.FULL

    await db.flush()
    await db.refresh(join_request)
    return join_request


async def get_user_requests(
    user: User,
    db: AsyncSession,
    direction: str = "sent",
) -> list[JoinRequestResponse]:
    """Get join requests sent by or received by the user."""
    if direction == "sent":
        result = await db.execute(
            select(JoinRequest)
            .where(JoinRequest.requester_id == user.id)
            .order_by(JoinRequest.created_at.desc())
        )
    else:
        # Received = requests to sessions I host
        result = await db.execute(
            select(JoinRequest)
            .join(StudySession)
            .where(StudySession.host_id == user.id)
            .order_by(JoinRequest.created_at.desc())
        )

    requests = result.scalars().all()

    return [
        JoinRequestResponse(
            id=r.id,
            session_id=r.session_id,
            session_subject=r.session.subject,
            session_scheduled_at=r.session.scheduled_at,
            requester_id=r.requester_id,
            requester_name=r.requester.full_name,
            requester_department=r.requester.department,
            requester_year=r.requester.year,
            requester_avatar=r.requester.avatar_url,
            status=r.status,
            message=r.message,
            created_at=r.created_at,
        )
        for r in requests
    ]
