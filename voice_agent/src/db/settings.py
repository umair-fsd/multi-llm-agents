"""Settings service for reading app configuration from database."""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import DATABASE_URL

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for reading application settings from database."""

    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._cache = {}  # Simple cache to avoid repeated DB calls

    async def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value from database."""
        # Check cache first (refreshed per session)
        if key in self._cache:
            return self._cache[key]
        
        try:
            async with self.async_session_maker() as db:
                result = await db.execute(
                    text("SELECT value FROM app_settings WHERE key = :key"),
                    {"key": key}
                )
                row = result.fetchone()
                value = row[0] if row else default
                self._cache[key] = value
                return value
        except Exception as e:
            logger.error(f"Error reading setting {key}: {e}")
            return default

    async def get_search_provider(self) -> str:
        """Get the configured search provider."""
        provider = await self.get_setting("search_provider", "duckduckgo")
        logger.info(f"🔍 Search provider from DB: {provider}")
        return provider

    def clear_cache(self):
        """Clear the settings cache."""
        self._cache = {}


# Singleton instance
settings_service = SettingsService()

