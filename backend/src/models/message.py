"""Message model - conversation messages."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class MessageRole(str, Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """Conversation message."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Audio info (if applicable)
    audio_duration_ms: Mapped[int] = mapped_column(nullable=True)
    
    # Tools used for this message (e.g., ['web_search', 'rag'])
    tools_used: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    
    # Message metadata (audio duration, agent name, etc)
    message_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    session = relationship("Session", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"
