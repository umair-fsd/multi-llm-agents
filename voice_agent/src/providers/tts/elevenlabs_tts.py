"""ElevenLabs TTS Provider."""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Check if elevenlabs plugin is available
try:
    from livekit.plugins import elevenlabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logger.warning("livekit-plugins-elevenlabs not installed")


def create_elevenlabs_tts(
    voice: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Create an ElevenLabs TTS instance.
    
    Args:
        voice: Voice ID or name to use
        api_key: Optional API key override
        
    Returns:
        ElevenLabs TTS instance
    """
    if not ELEVENLABS_AVAILABLE:
        raise ImportError(
            "ElevenLabs TTS requires livekit-plugins-elevenlabs. "
            "Install with: pip install livekit-plugins-elevenlabs"
        )
    
    key = api_key or os.getenv("ELEVENLABS_API_KEY")
    
    if not key:
        raise ValueError("ELEVENLABS_API_KEY not configured")
    
    voice = voice or "Rachel"
    
    logger.info(f"Creating ElevenLabs TTS with voice: {voice}")
    
    return elevenlabs.TTS(
        voice=voice,
        api_key=key,
    )

