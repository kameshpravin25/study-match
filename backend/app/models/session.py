import uuid
import enum
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base, TimestampMixin


class SessionType(str, enum.Enum):
    ONLINE = "online"
    IN_PERSON = "in_person"


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ANY = "any"


class SessionStatus(str, enum.Enum):
    OPEN = "open"
    FULL = "full"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class StudySession(Base, TimestampMixin):
    __tablename__ = "study_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    host_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meet_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_participants: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
    )
    skill_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="any"
    )
    campus: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )

    # Relationships
    host = relationship("User", back_populates="hosted_sessions", lazy="selectin")
    join_requests = relationship(
        "JoinRequest", back_populates="session", lazy="selectin"
    )
    participants = relationship(
        "SessionParticipant",
        back_populates="session",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StudySession {self.subject} by {self.host_id}>"


class JoinRequest(Base, TimestampMixin):
    __tablename__ = "join_requests"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requester_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    session = relationship("StudySession", back_populates="join_requests")
    requester = relationship("User", back_populates="join_requests")

    def __repr__(self) -> str:
        return f"<JoinRequest {self.requester_id} -> {self.session_id}>"


class SessionParticipant(Base):
    __tablename__ = "session_participants"

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    session = relationship("StudySession", back_populates="participants")
    user = relationship("User", back_populates="participations")
