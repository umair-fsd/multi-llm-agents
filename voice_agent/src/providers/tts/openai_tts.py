"""OpenAI TTS Provider."""

import os
import logging
from typing import Optional

from livekit.plugins import openai

logger = logging.getLogger(__name__)


def create_openai_tts(
    voice: Optional[str] = None,
    api_key: Optional[str] = None,
) -> openai.TTS:
    """
    Create an OpenAI TTS instance.
    
    Args:
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        api_key: Optional API key override
        
    Returns:
        OpenAI TTS instance
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    
    if not key:
        raise ValueError("OPENAI_API_KEY not configured")
    
    voice = voice or "alloy"
    
    logger.info(f"Creating OpenAI TTS with voice: {voice}")
    
    return openai.TTS(
        voice=voice,
        api_key=key,
    )

