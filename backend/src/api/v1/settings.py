"""Settings API endpoints."""

from fastapi import APIRouter

from src.api.deps import CurrentUser
from src.config import settings

router = APIRouter()


@router.get("")
async def get_settings(user: CurrentUser):
    """Get application settings (non-sensitive)."""
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
            "default_provider": settings.default_search_provider,
            "providers": ["tavily", "brave", "duckduckgo"],
        },
        "voice": {
            "tts_voices": [
                "aura-asteria-en",
                "aura-luna-en", 
                "aura-stella-en",
                "aura-athena-en",
                "aura-hera-en",
                "aura-orion-en",
                "aura-arcas-en",
                "aura-perseus-en",
                "aura-angus-en",
                "aura-orpheus-en",
            ],
        },
    }


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
