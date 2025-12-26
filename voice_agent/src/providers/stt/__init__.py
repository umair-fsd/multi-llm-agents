"""
Speech-to-Text (STT) Providers.

Supported providers:
- openai: OpenAI Whisper (paid, high accuracy)
- deepgram: Deepgram Nova (paid, very fast, real-time)
"""

import logging
from typing import Optional

from livekit.agents import stt

logger = logging.getLogger(__name__)

# Registry of available STT providers
STT_PROVIDERS = {
    "openai": {
        "name": "OpenAI Whisper",
        "description": "High-accuracy speech recognition from OpenAI",
        "languages": ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "zh", "ja", "ko"],
        "requires_key": "OPENAI_API_KEY",
    },
    "deepgram": {
        "name": "Deepgram Nova",
        "description": "Ultra-fast real-time speech recognition",
        "languages": ["en", "es", "fr", "de", "it", "pt", "nl", "hi", "ja", "ko", "zh"],
        "requires_key": "DEEPGRAM_API_KEY",
    },
}


def get_stt_provider(
    provider: str = "deepgram",
    language: str = "en",
    api_key: Optional[str] = None,
) -> Optional[stt.STT]:
    """
    Get an STT provider instance.
    
    Args:
        provider: Provider name (openai, deepgram)
        language: Language code
        api_key: Optional API key override
        
    Returns:
        STT instance or None if provider unavailable
    """
    try:
        if provider == "openai":
            from .openai_stt import create_openai_stt
            return create_openai_stt(language=language, api_key=api_key)
            
        elif provider == "deepgram":
            from .deepgram_stt import create_deepgram_stt
            return create_deepgram_stt(language=language, api_key=api_key)
            
        else:
            logger.error(f"Unknown STT provider: {provider}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create STT provider '{provider}': {e}")
        return None

