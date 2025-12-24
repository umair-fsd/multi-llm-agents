"""Session model - voice conversation sessions."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class Session(Base):
    """Voice conversation session."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Allow anonymous sessions for now
    )
    
    # LiveKit room info
    room_name: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Participant info
    participant_name: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Session status (active, ended)
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="active",
        server_default="active",
    )
    
    # Session metadata
    session_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    ended_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, room={self.room_name}, status={self.status})>"
