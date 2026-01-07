"""Deepgram STT Provider (Nova)."""

import os
import logging
from typing import Optional

from livekit.plugins import deepgram

logger = logging.getLogger(__name__)


def create_deepgram_stt(
    language: str = "en",
    api_key: Optional[str] = None,
) -> deepgram.STT:
    """
    Create a Deepgram STT (Nova) instance.
    
    Args:
        language: Language code
        api_key: Optional API key override
        
    Returns:
        Deepgram STT instance
    """
    key = api_key or os.getenv("DEEPGRAM_API_KEY")
    
    if not key:
        raise ValueError("DEEPGRAM_API_KEY not configured")
    
    logger.info(f"Creating Deepgram STT (Nova) with language: {language}")
    
    return deepgram.STT(
        language=language,
        api_key=key,
    )

