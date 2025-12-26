"""
Text-to-Speech (TTS) Providers.

Supported providers:
- openai: OpenAI TTS (paid, high quality)
- deepgram: Deepgram Aura TTS (paid, fast)
- elevenlabs: ElevenLabs TTS (freemium, very natural)
"""

import logging
from typing import Optional

from livekit.agents import tts

logger = logging.getLogger(__name__)

# Registry of available TTS providers
TTS_PROVIDERS = {
    "openai": {
        "name": "OpenAI TTS",
        "description": "High-quality TTS from OpenAI",
        "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        "requires_key": "OPENAI_API_KEY",
    },
    "deepgram": {
        "name": "Deepgram Aura",
        "description": "Fast, low-latency TTS from Deepgram",
        "voices": ["aura-2-andromeda-en", "aura-2-arcas-en", "aura-2-athena-en", "aura-2-helios-en", "aura-2-hera-en", "aura-2-luna-en", "aura-2-orion-en", "aura-2-perseus-en", "aura-2-stella-en", "aura-2-zeus-en"],
        "requires_key": "DEEPGRAM_API_KEY",
    },
    "elevenlabs": {
        "name": "ElevenLabs",
        "description": "Natural-sounding TTS (10k chars/month free)",
        "voices": ["Rachel", "Domi", "Bella", "Antoni", "Elli", "Josh", "Arnold", "Adam", "Sam"],
        "requires_key": "ELEVENLABS_API_KEY",
    },
}


def get_tts_provider(
    provider: str = "openai",
    voice: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[tts.TTS]:
    """
    Get a TTS provider instance.
    
    Args:
        provider: Provider name (openai, deepgram, elevenlabs)
        voice: Voice ID/name to use
        api_key: Optional API key override
        
    Returns:
        TTS instance or None if provider unavailable
    """
    try:
        if provider == "openai":
            from .openai_tts import create_openai_tts
            return create_openai_tts(voice=voice, api_key=api_key)
            
        elif provider == "deepgram":
            from .deepgram_tts import create_deepgram_tts
            return create_deepgram_tts(voice=voice, api_key=api_key)
            
        elif provider == "elevenlabs":
            from .elevenlabs_tts import create_elevenlabs_tts
            return create_elevenlabs_tts(voice=voice, api_key=api_key)
            
        else:
            logger.error(f"Unknown TTS provider: {provider}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create TTS provider '{provider}': {e}")
        return None

