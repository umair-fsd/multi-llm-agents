"""Session history service for storing conversations - uses direct SQL."""

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import DATABASE_URL


class SessionHistoryService:
    """Service for storing voice conversation history."""

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
        user_id: str = None,
        metadata: dict = None,
    ) -> str:
        """Create a new session and return its UUID."""
        session_id = str(uuid.uuid4())
        
        async with self.async_session_maker() as db:
            await db.execute(
                text("""
                    INSERT INTO sessions (id, room_name, user_id, session_metadata, started_at)
                    VALUES (:id, :room_name, :user_id, :metadata, :started_at)
                """),
                {
                    "id": session_id,
                    "room_name": room_name,
                    "user_id": user_id,
                    "metadata": json.dumps(metadata or {}),  # Serialize dict to JSON string for asyncpg
                    "started_at": datetime.utcnow(),
                }
            )
            await db.commit()
            return session_id

    async def end_session(self, session_id: str):
        """Mark a session as ended."""
        async with self.async_session_maker() as db:
            await db.execute(
                text("""
                    UPDATE sessions 
                    SET ended_at = :ended_at
                    WHERE id = :session_id
                """),
                {
                    "session_id": session_id,
                    "ended_at": datetime.utcnow(),
                }
            )
            await db.commit()

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_id: str = None,
        audio_duration_ms: int = None,
        metadata: dict = None,
    ):
        """Add a message to a session."""
        message_id = str(uuid.uuid4())
        
        async with self.async_session_maker() as db:
            await db.execute(
                text("""
                    INSERT INTO messages (id, session_id, agent_id, role, content, 
                                          audio_duration_ms, message_metadata, created_at)
                    VALUES (:id, :session_id, :agent_id, :role, :content, 
                            :audio_duration_ms, :metadata, :created_at)
                """),
                {
                    "id": message_id,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "role": role,
                    "content": content,
                    "audio_duration_ms": audio_duration_ms,
                    "metadata": json.dumps(metadata or {}),  # Serialize dict to JSON string for asyncpg
                    "created_at": datetime.utcnow(),
                }
            )
            await db.commit()


# Singleton instance
session_history_service = SessionHistoryService()
