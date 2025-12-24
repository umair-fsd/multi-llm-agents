"""Session history service for storing conversations with full tracking."""

import json
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import DATABASE_URL


class SessionHistoryService:
    """Service for storing voice conversation history with agent and tool tracking."""

    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_session(
        self,
        room_name: str,
        participant_name: str = None,
        user_id: str = None,
        metadata: dict = None,
    ) -> str:
        """Create a new session with participant info."""
        session_id = str(uuid.uuid4())
        
        async with self.async_session_maker() as db:
            await db.execute(
                text("""
                    INSERT INTO sessions (id, room_name, user_id, participant_name, status, session_metadata, started_at)
                    VALUES (:id, :room_name, :user_id, :participant_name, :status, :metadata, :started_at)
                """),
                {
                    "id": session_id,
                    "room_name": room_name,
                    "user_id": user_id,
                    "participant_name": participant_name,
                    "status": "active",
                    "metadata": json.dumps(metadata or {}),
                    "started_at": datetime.utcnow(),
                }
            )
            await db.commit()
            return session_id

    async def end_session(self, session_id: str, reason: str = None):
        """Mark a session as ended."""
        async with self.async_session_maker() as db:
            # First get current metadata
            result = await db.execute(
                text("SELECT session_metadata FROM sessions WHERE id = :session_id"),
                {"session_id": session_id}
            )
            row = result.fetchone()
            
            metadata = {}
            if row and row[0]:
                metadata = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            
            if reason:
                metadata['end_reason'] = reason
            
            await db.execute(
                text("""
                    UPDATE sessions 
                    SET ended_at = :ended_at, status = :status, session_metadata = :metadata
                    WHERE id = :session_id
                """),
                {
                    "session_id": session_id,
                    "ended_at": datetime.utcnow(),
                    "status": "ended",
                    "metadata": json.dumps(metadata),
                }
            )
            await db.commit()

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_id: str = None,
        agent_name: str = None,
        tools_used: List[str] = None,
        audio_duration_ms: int = None,
        metadata: dict = None,
    ):
        """Add a message with agent and tool tracking."""
        message_id = str(uuid.uuid4())
        
        # Build message metadata
        msg_metadata = metadata or {}
        if agent_name:
            msg_metadata['agent_name'] = agent_name
        if tools_used:
            msg_metadata['tools_used'] = tools_used
        
        async with self.async_session_maker() as db:
            await db.execute(
                text("""
                    INSERT INTO messages (id, session_id, agent_id, role, content, 
                                          audio_duration_ms, tools_used, message_metadata, created_at)
                    VALUES (:id, :session_id, :agent_id, :role, :content, 
                            :audio_duration_ms, :tools_used, :metadata, :created_at)
                """),
                {
                    "id": message_id,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "role": role,
                    "content": content,
                    "audio_duration_ms": audio_duration_ms,
                    "tools_used": json.dumps(tools_used or []),
                    "metadata": json.dumps(msg_metadata),
                    "created_at": datetime.utcnow(),
                }
            )
            await db.commit()
            return message_id

    async def update_session_metadata(self, session_id: str, updates: dict):
        """Update session metadata (e.g., add agents used, total messages, etc.)."""
        async with self.async_session_maker() as db:
            # Get current metadata
            result = await db.execute(
                text("SELECT session_metadata FROM sessions WHERE id = :session_id"),
                {"session_id": session_id}
            )
            row = result.fetchone()
            
            metadata = {}
            if row and row[0]:
                metadata = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            
            # Merge updates
            metadata.update(updates)
            
            await db.execute(
                text("""
                    UPDATE sessions 
                    SET session_metadata = :metadata
                    WHERE id = :session_id
                """),
                {
                    "session_id": session_id,
                    "metadata": json.dumps(metadata),
                }
            )
            await db.commit()


# Singleton instance
session_history_service = SessionHistoryService()
