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
    
    # Get all provider settings from database
    search_provider = await get_setting_from_db(db, "search_provider") or settings.default_search_provider
    llm_provider = await get_setting_from_db(db, "llm_provider") or "groq"
    llm_model = await get_setting_from_db(db, "llm_model") or "llama-3.3-70b-versatile"
    tts_provider = await get_setting_from_db(db, "tts_provider") or "deepgram"
    tts_voice = await get_setting_from_db(db, "tts_voice") or "aura-2-andromeda-en"
    stt_provider = await get_setting_from_db(db, "stt_provider") or "deepgram"
    
    return {
        "environment": settings.environment,
        "llm": {
            "default_provider": llm_provider,
            "default_model": llm_model,
            "providers": {
                "openai": {
                    "name": "OpenAI",
                    "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                    "configured": bool(settings.openai_api_key),
                },
                "groq": {
                    "name": "Groq (FREE)",
                    "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-8b-8192", "mixtral-8x7b-32768"],
                    "configured": bool(settings.groq_api_key),
                },
                "openrouter": {
                    "name": "OpenRouter",
                    "models": ["anthropic/claude-3.5-sonnet", "google/gemini-pro", "meta-llama/llama-3.1-70b-instruct"],
                    "configured": bool(settings.openrouter_api_key),
                },
            },
        },
        "tts": {
            "default_provider": tts_provider,
            "default_voice": tts_voice,
            "providers": {
                "openai": {
                    "name": "OpenAI TTS",
                    "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                    "configured": bool(settings.openai_api_key),
                },
                "deepgram": {
                    "name": "Deepgram Aura",
                    "voices": ["aura-2-andromeda-en", "aura-2-arcas-en", "aura-2-athena-en", "aura-2-helios-en", "aura-2-hera-en", "aura-2-luna-en", "aura-2-orion-en", "aura-2-perseus-en", "aura-2-stella-en", "aura-2-zeus-en"],
                    "configured": bool(settings.deepgram_api_key),
                },
                "elevenlabs": {
                    "name": "ElevenLabs",
                    "voices": ["Rachel", "Domi", "Bella", "Antoni", "Elli", "Josh", "Arnold", "Adam", "Sam"],
                    "configured": bool(getattr(settings, 'elevenlabs_api_key', '')),
                },
            },
        },
        "stt": {
            "default_provider": stt_provider,
            "providers": {
                "openai": {
                    "name": "OpenAI Whisper",
                    "configured": bool(settings.openai_api_key),
                },
                "deepgram": {
                    "name": "Deepgram Nova",
                    "configured": bool(settings.deepgram_api_key),
                },
            },
        },
        "search": {
            "default_provider": search_provider,
            "providers": {
                "duckduckgo": {
                    "name": "DuckDuckGo",
                    "configured": True,
                },
                "tavily": {
                    "name": "Tavily",
                    "configured": bool(settings.tavily_api_key),
                },
                "brave": {
                    "name": "Brave Search",
                    "configured": bool(settings.brave_api_key),
                },
            },
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


@router.put("/llm-provider")
async def update_llm_provider(
    update: SettingUpdate,
    user: CurrentUser,
    db: DbSession,
):
    """Update the LLM provider setting."""
    valid_providers = ["openai", "groq", "openrouter"]
    
    if update.value not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {valid_providers}"
        )
    
    # Check if API key is configured
    if update.value == "openai" and not settings.openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY is not configured in environment"
        )
    if update.value == "groq" and not settings.groq_api_key:
        raise HTTPException(
            status_code=400,
            detail="GROQ_API_KEY is not configured in environment"
        )
    if update.value == "openrouter" and not settings.openrouter_api_key:
        raise HTTPException(
            status_code=400,
            detail="OPENROUTER_API_KEY is not configured in environment"
        )
    
    await set_setting_in_db(
        db, 
        "llm_provider", 
        update.value,
        f"LLM provider: {update.value}"
    )
    
    return {"key": "llm_provider", "value": update.value}


@router.put("/llm-model")
async def update_llm_model(
    update: SettingUpdate,
    user: CurrentUser,
    db: DbSession,
):
    """Update the LLM model setting."""
    # Get current provider to validate model
    provider = await get_setting_from_db(db, "llm_provider")
    if not provider:
        provider = settings.default_llm_provider
    
    valid_models = {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "openrouter": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-pro"],
    }
    
    if provider not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {provider}"
        )
    
    if update.value not in valid_models[provider]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model for {provider}. Must be one of: {valid_models[provider]}"
        )
    
    await set_setting_in_db(
        db, 
        "llm_model", 
        update.value,
        f"LLM model: {update.value}"
    )
    
    return {"key": "llm_model", "value": update.value}


@router.get("/llm-provider")
async def get_llm_provider(db: DbSession):
    """Get the current LLM provider (public endpoint for voice agent)."""
    provider = await get_setting_from_db(db, "llm_provider")
    model = await get_setting_from_db(db, "llm_model")
    return {
        "provider": provider or "groq",
        "model": model or "llama-3.3-70b-versatile"
    }


@router.put("/tts-provider")
async def update_tts_provider(
    update: SettingUpdate,
    user: CurrentUser,
    db: DbSession,
):
    """Update the TTS provider setting."""
    valid_providers = ["openai", "deepgram", "elevenlabs"]
    
    if update.value not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {valid_providers}"
        )
    
    # Check if API key is configured
    if update.value == "openai" and not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")
    if update.value == "deepgram" and not settings.deepgram_api_key:
        raise HTTPException(status_code=400, detail="DEEPGRAM_API_KEY is not configured")
    if update.value == "elevenlabs" and not getattr(settings, 'elevenlabs_api_key', ''):
        raise HTTPException(status_code=400, detail="ELEVENLABS_API_KEY is not configured")
    
    await set_setting_in_db(db, "tts_provider", update.value, f"TTS provider: {update.value}")
    return {"key": "tts_provider", "value": update.value}


@router.put("/tts-voice")
async def update_tts_voice(
    update: SettingUpdate,
    user: CurrentUser,
    db: DbSession,
):
    """Update the TTS voice setting."""
    await set_setting_in_db(db, "tts_voice", update.value, f"TTS voice: {update.value}")
    return {"key": "tts_voice", "value": update.value}


@router.put("/stt-provider")
async def update_stt_provider(
    update: SettingUpdate,
    user: CurrentUser,
    db: DbSession,
):
    """Update the STT provider setting."""
    valid_providers = ["openai", "deepgram"]
    
    if update.value not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {valid_providers}"
        )
    
    # Check if API key is configured
    if update.value == "openai" and not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")
    if update.value == "deepgram" and not settings.deepgram_api_key:
        raise HTTPException(status_code=400, detail="DEEPGRAM_API_KEY is not configured")
    
    await set_setting_in_db(db, "stt_provider", update.value, f"STT provider: {update.value}")
    return {"key": "stt_provider", "value": update.value}


@router.get("/voice-providers")
async def get_voice_providers(db: DbSession):
    """Get current voice provider settings (public endpoint for voice agent)."""
    tts_provider = await get_setting_from_db(db, "tts_provider") or "deepgram"
    tts_voice = await get_setting_from_db(db, "tts_voice") or "aura-2-andromeda-en"
    stt_provider = await get_setting_from_db(db, "stt_provider") or "deepgram"
    llm_provider = await get_setting_from_db(db, "llm_provider") or "groq"
    llm_model = await get_setting_from_db(db, "llm_model") or "llama-3.3-70b-versatile"
    
    return {
        "tts": {"provider": tts_provider, "voice": tts_voice},
        "stt": {"provider": stt_provider},
        "llm": {"provider": llm_provider, "model": llm_model},
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
