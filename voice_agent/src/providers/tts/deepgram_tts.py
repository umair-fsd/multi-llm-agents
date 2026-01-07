"""Deepgram TTS Provider."""

import os
import logging
from typing import Optional

from livekit.plugins import deepgram

logger = logging.getLogger(__name__)


def create_deepgram_tts(
    voice: Optional[str] = None,
    api_key: Optional[str] = None,
) -> deepgram.TTS:
    """
    Create a Deepgram TTS instance.
    
    Args:
        voice: Voice/model to use (aura-asteria-en, aura-2-andromeda-en, etc.)
        api_key: Optional API key override
        
    Returns:
        Deepgram TTS instance
    """
    key = api_key or os.getenv("DEEPGRAM_API_KEY")
    
    if not key:
        raise ValueError("DEEPGRAM_API_KEY not configured")
    
    # Deepgram uses 'model' parameter, not 'voice'
    # Default to aura-2-andromeda-en (newer, better quality)
    model = voice or "aura-2-andromeda-en"
    
    logger.info(f"Creating Deepgram TTS with model: {model}")
    
    return deepgram.TTS(
        model=model,
        api_key=key,
    )

