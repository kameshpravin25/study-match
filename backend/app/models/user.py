import uuid
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    campus: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Bengaluru"
    )
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Relationships
    hosted_sessions = relationship(
        "StudySession", back_populates="host", lazy="selectin"
    )
    join_requests = relationship(
        "JoinRequest", back_populates="requester", lazy="selectin"
    )
    participations = relationship(
        "SessionParticipant", back_populates="user", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.full_name} ({self.email})>"
