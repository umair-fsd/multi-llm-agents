"""Document schemas - request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    """Schema for document creation (metadata only, file uploaded separately)."""
    agent_id: UUID


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    agent_id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents."""
    items: list[DocumentResponse]
    total: int
