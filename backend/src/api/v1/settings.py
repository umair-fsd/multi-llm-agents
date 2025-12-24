"""Settings API endpoints - configurable from admin panel."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from src.api.deps import CurrentUser, DbSession
from src.config import settings

router = APIRouter()


class SettingUpdate(BaseModel):
    """Request to update a setting."""
    value: str


class SettingResponse(BaseModel):
    """Response for a single setting."""
    key: str
    value: str
    description: str | None = None


async def get_setting_from_db(db, key: str) -> str | None:
    """Get a setting value from database."""
    result = await db.execute(
        text("SELECT value FROM app_settings WHERE key = :key"),
        {"key": key}
    )
    row = result.fetchone()
    return row[0] if row else None


async def set_setting_in_db(db, key: str, value: str, description: str = None):
    """Set a setting value in database."""
    await db.execute(
        text("""
            INSERT INTO app_settings (key, value, description, updated_at) 
            VALUES (:key, :value, :description, NOW())
            ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
        """),
        {"key": key, "value": value, "description": description}
    )
    await db.flush()


@router.get("")
async def get_settings(user: CurrentUser, db: DbSession):
    """Get application settings (reads from database for configurable ones)."""
    
    # Get search provider from database
    search_provider = await get_setting_from_db(db, "search_provider")
    if not search_provider:
        search_provider = settings.default_search_provider
    
    return {
        "environment": settings.environment,
        "llm": {
            "default_provider": settings.default_llm_provider,
            "default_model": settings.default_llm_model,
            "providers": ["openai", "openrouter"],
            "models": {
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "openrouter": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-pro"],
            },
        },
        "search": {
            "default_provider": search_provider,
            "providers": ["tavily", "brave", "duckduckgo"],
            "api_keys_configured": {
                "tavily": bool(settings.tavily_api_key),
                "brave": bool(settings.brave_api_key),
                "duckduckgo": True,  # No API key needed
            },
        },
        "voice": {
            "tts_voices": [
                "alloy", "echo", "fable", "onyx", "nova", "shimmer"
            ],
        },
    }


@router.put("/search-provider")
async def update_search_provider(
    update: SettingUpdate,
    user: CurrentUser,
    db: DbSession,
):
    """Update the search provider setting."""
    valid_providers = ["tavily", "brave", "duckduckgo"]
    
    if update.value not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {valid_providers}"
        )
    
    # Check if API key is configured for non-duckduckgo providers
    if update.value == "tavily" and not settings.tavily_api_key:
        raise HTTPException(
            status_code=400,
            detail="TAVILY_API_KEY is not configured in environment"
        )
    if update.value == "brave" and not settings.brave_api_key:
        raise HTTPException(
            status_code=400,
            detail="BRAVE_API_KEY is not configured in environment"
        )
    
    await set_setting_in_db(
        db, 
        "search_provider", 
        update.value,
        "Web search provider: tavily, brave, or duckduckgo"
    )
    
    return {"key": "search_provider", "value": update.value}


@router.get("/search-provider")
async def get_search_provider(db: DbSession):
    """Get the current search provider (public endpoint for voice agent)."""
    provider = await get_setting_from_db(db, "search_provider")
    return {"provider": provider or "duckduckgo"}


@router.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "livekit": settings.livekit_url,
            "qdrant": f"{settings.qdrant_host}:{settings.qdrant_port}",
        },
    }
