"""OpenAI STT Provider (Whisper)."""

import os
import logging
from typing import Optional

from livekit.plugins import openai

logger = logging.getLogger(__name__)


def create_openai_stt(
    language: str = "en",
    api_key: Optional[str] = None,
) -> openai.STT:
    """
    Create an OpenAI STT (Whisper) instance.
    
    Args:
        language: Language code
        api_key: Optional API key override
        
    Returns:
        OpenAI STT instance
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    
    if not key:
        raise ValueError("OPENAI_API_KEY not configured")
    
    logger.info(f"Creating OpenAI STT (Whisper) with language: {language}")
    
    return openai.STT(
        language=language,
        api_key=key,
    )

