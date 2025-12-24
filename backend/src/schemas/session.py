"""Session schemas - request/response models."""

from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: UUID
    role: str
    content: str
    agent_id: UUID | None
    agent_name: str | None = None
    audio_duration_ms: int | None
    tools_used: list[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Schema for session response."""
    id: UUID
    user_id: UUID | None
    room_name: str | None
    participant_name: str | None = None
    status: str = "active"
    started_at: datetime
    ended_at: datetime | None
    message_count: int = 0
    metadata: dict[str, Any] = {}

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    """Schema for session with messages."""
    messages: list[MessageResponse] = []


class SessionListResponse(BaseModel):
    """Schema for list of sessions."""
    items: list[SessionResponse]
    total: int
    page: int
    page_size: int


class EndSessionRequest(BaseModel):
    """Request to end a session."""
    reason: str | None = None
