"""Session schemas - request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: UUID
    role: str
    content: str
    agent_id: UUID | None
    audio_duration_ms: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Schema for session response."""
    id: UUID
    user_id: UUID | None
    room_name: str | None
    started_at: datetime
    ended_at: datetime | None
    message_count: int = 0

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
