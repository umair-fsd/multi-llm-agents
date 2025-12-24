"""Database service for voice agent - uses direct SQL queries."""

import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import DATABASE_URL


class AgentDBService:
    """Service for loading agent configurations from database."""

    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_agent_config(self, agent_id: str) -> Optional[dict]:
        """Load agent configuration from database by ID."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                text("""
                    SELECT id, name, description, system_prompt, 
                           model_settings, capabilities, voice_settings
                    FROM agents 
                    WHERE id = :agent_id AND is_active = true
                """),
                {"agent_id": agent_id}
            )
            row = result.fetchone()
            
            if not row:
                return None
            
            return {
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "system_prompt": row.system_prompt,
                "model_settings": row.model_settings or {},
                "capabilities": row.capabilities or {},
                "voice_settings": row.voice_settings or {},
            }

    async def get_default_agent(self) -> Optional[dict]:
        """Get the default agent configuration."""
        async with self.async_session_maker() as session:
            # Try to get default agent first
            result = await session.execute(
                text("""
                    SELECT id, name, description, system_prompt, 
                           model_settings, capabilities, voice_settings
                    FROM agents 
                    WHERE is_default = true AND is_active = true
                    LIMIT 1
                """)
            )
            row = result.fetchone()
            
            # If no default, get first active agent
            if not row:
                result = await session.execute(
                    text("""
                        SELECT id, name, description, system_prompt, 
                               model_settings, capabilities, voice_settings
                        FROM agents 
                        WHERE is_active = true
                        ORDER BY created_at ASC
                        LIMIT 1
                    """)
                )
                row = result.fetchone()
            
            if not row:
                return None
            
            return {
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "system_prompt": row.system_prompt,
                "model_settings": row.model_settings or {},
                "capabilities": row.capabilities or {},
                "voice_settings": row.voice_settings or {},
            }

    async def get_all_agents(self) -> list[dict]:
        """Get all active agents for dynamic routing."""
        async with self.async_session_maker() as session:
            result = await session.execute(
                text("""
                    SELECT id, name, description, system_prompt, 
                           model_settings, capabilities, voice_settings
                    FROM agents 
                    WHERE is_active = true
                    ORDER BY is_default DESC, name ASC
                """)
            )
            rows = result.fetchall()
            
            return [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "system_prompt": row.system_prompt,
                    "model_settings": row.model_settings or {},
                    "capabilities": row.capabilities or {},
                    "voice_settings": row.voice_settings or {},
                }
                for row in rows
            ]


# Singleton instance
agent_db_service = AgentDBService()
