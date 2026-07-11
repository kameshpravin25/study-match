from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.session import StudySession, JoinRequest, SessionParticipant

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_PASSWORD = "studymatch2026"  # Change this before going live


def verify_admin(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password")
    return True


@router.get("/stats")
async def get_stats(password: str, db: AsyncSession = Depends(get_db)):
    verify_admin(password)

    total_users = await db.scalar(select(func.count(User.id)))
    total_sessions = await db.scalar(select(func.count(StudySession.id)))
    total_requests = await db.scalar(select(func.count(JoinRequest.id)))
    total_participants = await db.scalar(
        select(func.count(SessionParticipant.user_id))
    )

    # Active sessions (open status, scheduled in the future)
    active_sessions = await db.scalar(
        select(func.count(StudySession.id)).where(
            StudySession.status == "open",
        )
    )

    # Sessions by type
    online_count = await db.scalar(
        select(func.count(StudySession.id)).where(
            StudySession.session_type == "online"
        )
    )
    in_person_count = await db.scalar(
        select(func.count(StudySession.id)).where(
            StudySession.session_type == "in_person"
        )
    )

    # Requests by status
    pending_requests = await db.scalar(
        select(func.count(JoinRequest.id)).where(
            JoinRequest.status == "pending"
        )
    )
    accepted_requests = await db.scalar(
        select(func.count(JoinRequest.id)).where(
            JoinRequest.status == "accepted"
        )
    )
    rejected_requests = await db.scalar(
        select(func.count(JoinRequest.id)).where(
            JoinRequest.status == "rejected"
        )
    )

    return {
        "total_users": total_users or 0,
        "total_sessions": total_sessions or 0,
        "total_requests": total_requests or 0,
        "total_participants": total_participants or 0,
        "active_sessions": active_sessions or 0,
        "online_sessions": online_count or 0,
        "in_person_sessions": in_person_count or 0,
        "pending_requests": pending_requests or 0,
        "accepted_requests": accepted_requests or 0,
        "rejected_requests": rejected_requests or 0,
    }


@router.get("/users")
async def get_all_users(password: str, db: AsyncSession = Depends(get_db)):
    verify_admin(password)

    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "department": u.department,
            "year": u.year,
            "campus": u.campus,
            "bio": u.bio,
            "is_verified": u.is_verified,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.get("/sessions")
async def get_all_sessions(
    password: str, db: AsyncSession = Depends(get_db)
):
    verify_admin(password)

    result = await db.execute(
        select(StudySession).order_by(StudySession.created_at.desc())
    )
    sessions = result.scalars().all()

    data = []
    for s in sessions:
        # Count participants
        part_count = await db.scalar(
            select(func.count(SessionParticipant.user_id)).where(
                SessionParticipant.session_id == s.id
            )
        )
        # Count requests
        req_count = await db.scalar(
            select(func.count(JoinRequest.id)).where(
                JoinRequest.session_id == s.id
            )
        )
        # Get host name
        host = await db.get(User, s.host_id)

        data.append(
            {
                "id": s.id,
                "subject": s.subject,
                "topic": s.topic,
                "description": s.description,
                "session_type": s.session_type,
                "location": s.location,
                "meet_link": s.meet_link,
                "scheduled_at": s.scheduled_at.isoformat()
                    if s.scheduled_at else None,
                "duration_minutes": s.duration_minutes,
                "max_participants": s.max_participants,
                "skill_level": s.skill_level,
                "campus": s.campus,
                "status": s.status,
                "host_name": host.full_name if host else "Unknown",
                "host_email": host.email if host else "Unknown",
                "participant_count": part_count or 0,
                "request_count": req_count or 0,
                "created_at": s.created_at.isoformat()
                    if s.created_at else None,
            }
        )

    return data


@router.get("/requests")
async def get_all_requests(
    password: str, db: AsyncSession = Depends(get_db)
):
    verify_admin(password)

    result = await db.execute(
        select(JoinRequest).order_by(JoinRequest.created_at.desc())
    )
    requests = result.scalars().all()

    data = []
    for r in requests:
        requester = await db.get(User, r.requester_id)
        session = await db.get(StudySession, r.session_id)

        data.append(
            {
                "id": r.id,
                "requester_name": requester.full_name
                    if requester else "Unknown",
                "requester_email": requester.email
                    if requester else "Unknown",
                "session_subject": session.subject if session else "Unknown",
                "session_id": r.session_id,
                "status": r.status,
                "message": r.message,
                "created_at": r.created_at.isoformat()
                    if r.created_at else None,
            }
        )

    return data
