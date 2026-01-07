"""OpenAI LLM Provider."""

import os
import logging
from typing import Optional

from livekit.plugins import openai

logger = logging.getLogger(__name__)


def create_openai_llm(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
) -> openai.LLM:
    """
    Create an OpenAI LLM instance.
    
    Args:
        model: Model to use (gpt-4o, gpt-4o-mini, etc.)
        api_key: Optional API key override
        temperature: Sampling temperature
        
    Returns:
        OpenAI LLM instance
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    
    if not key:
        raise ValueError("OPENAI_API_KEY not configured")
    
    model = model or "gpt-4o-mini"
    
    logger.info(f"Creating OpenAI LLM with model: {model}")
    
    return openai.LLM(
        model=model,
        api_key=key,
        temperature=temperature,
    )

