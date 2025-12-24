"""Session API endpoints for admin to view and manage voice sessions."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select, update

from src.api.deps import CurrentUser, DbSession
from src.models.session import Session
from src.models.message import Message
from src.models.agent import Agent
from src.schemas.session import (
    SessionListResponse, 
    SessionResponse, 
    SessionDetailResponse, 
    MessageResponse,
    EndSessionRequest,
)

router = APIRouter()


def session_to_response(session: Session, message_count: int = 0) -> SessionResponse:
    """Convert Session model to response schema."""
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        room_name=session.room_name,
        participant_name=getattr(session, 'participant_name', None),
        status=getattr(session, 'status', 'active') or 'active',
        started_at=session.started_at,
        ended_at=session.ended_at,
        message_count=message_count,
        metadata=session.session_metadata or {},
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    db: DbSession,
    user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
):
    """List all sessions with pagination. Optionally filter by status."""
    query = select(Session)
    
    # Filter by status if provided
    if status_filter:
        query = query.where(Session.status == status_filter)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    
    # Get paginated results
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Session.started_at.desc())
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Get message counts
    items = []
    for session in sessions:
        msg_count_query = select(func.count()).where(Message.session_id == session.id)
        msg_count = await db.scalar(msg_count_query) or 0
        items.append(session_to_response(session, msg_count))
    
    return SessionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/active", response_model=list[SessionResponse])
async def list_active_sessions(
    db: DbSession,
    user: CurrentUser,
):
    """List all currently active sessions."""
    query = select(Session).where(Session.status == 'active').order_by(Session.started_at.desc())
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    items = []
    for session in sessions:
        msg_count_query = select(func.count()).where(Message.session_id == session.id)
        msg_count = await db.scalar(msg_count_query) or 0
        items.append(session_to_response(session, msg_count))
    
    return items


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """Get a specific session with all messages and details."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Get messages with agent names
    msg_result = await db.execute(
        select(Message, Agent.name.label('agent_name'))
        .outerjoin(Agent, Message.agent_id == Agent.id)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages_data = msg_result.all()
    
    messages = []
    for row in messages_data:
        msg = row[0]  # Message object
        agent_name = row[1] if len(row) > 1 else None  # Agent name
        
        # Parse tools_used from message metadata or dedicated field
        tools_used = []
        if hasattr(msg, 'tools_used') and msg.tools_used:
            tools_used = msg.tools_used if isinstance(msg.tools_used, list) else []
        elif msg.message_metadata and isinstance(msg.message_metadata, dict):
            tools_used = msg.message_metadata.get('tools_used', [])
        
        messages.append(MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            agent_id=msg.agent_id,
            agent_name=agent_name,
            audio_duration_ms=msg.audio_duration_ms,
            tools_used=tools_used,
            created_at=msg.created_at,
        ))
    
    return SessionDetailResponse(
        id=session.id,
        user_id=session.user_id,
        room_name=session.room_name,
        participant_name=getattr(session, 'participant_name', None),
        status=getattr(session, 'status', 'active') or 'active',
        started_at=session.started_at,
        ended_at=session.ended_at,
        message_count=len(messages),
        metadata=session.session_metadata or {},
        messages=messages,
    )


@router.post("/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: UUID,
    db: DbSession,
    user: CurrentUser,
    request: EndSessionRequest | None = None,
):
    """End an active session."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    if session.status == 'ended':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already ended",
        )
    
    # Update session
    session.status = 'ended'
    session.ended_at = datetime.utcnow()
    
    # Store end reason in metadata if provided
    if request and request.reason:
        metadata = session.session_metadata or {}
        metadata['end_reason'] = request.reason
        session.session_metadata = metadata
    
    await db.flush()
    
    # Get message count
    msg_count_query = select(func.count()).where(Message.session_id == session.id)
    msg_count = await db.scalar(msg_count_query) or 0
    
    return session_to_response(session, msg_count)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """Delete a session and all its messages."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    await db.delete(session)
    await db.flush()
