"""Session API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from src.api.deps import CurrentUser, DbSession
from src.models.session import Session
from src.models.message import Message
from src.schemas.session import SessionListResponse, SessionResponse, SessionDetailResponse, MessageResponse

router = APIRouter()


def session_to_response(session: Session, message_count: int = 0) -> SessionResponse:
    """Convert Session model to response schema."""
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        room_name=session.room_name,
        started_at=session.started_at,
        ended_at=session.ended_at,
        message_count=message_count,
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    db: DbSession,
    user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
):
    """List all sessions with pagination."""
    query = select(Session)
    
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


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """Get a specific session with messages."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Get messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()
    
    return SessionDetailResponse(
        id=session.id,
        user_id=session.user_id,
        room_name=session.room_name,
        started_at=session.started_at,
        ended_at=session.ended_at,
        message_count=len(messages),
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                agent_id=msg.agent_id,
                audio_duration_ms=msg.audio_duration_ms,
                created_at=msg.created_at,
            )
            for msg in messages
        ],
    )


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
