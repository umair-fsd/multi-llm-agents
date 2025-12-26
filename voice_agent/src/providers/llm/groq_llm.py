"""Groq LLM Provider (FREE tier available)."""

import os
import logging
from typing import Optional

from livekit.plugins import openai

logger = logging.getLogger(__name__)


def create_groq_llm(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
) -> openai.LLM:
    """
    Create a Groq LLM instance.
    
    Uses OpenAI-compatible API endpoint.
    
    Args:
        model: Model to use (llama-3.1-70b-versatile, etc.)
        api_key: Optional API key override
        temperature: Sampling temperature
        
    Returns:
        LLM instance configured for Groq
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    
    if not key:
        raise ValueError("GROQ_API_KEY not configured")
    
    model = model or "llama-3.3-70b-versatile"
    
    logger.info(f"Creating Groq LLM with model: {model} (FREE tier)")
    
    # Groq uses OpenAI-compatible API
    return openai.LLM(
        model=model,
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
        temperature=temperature,
    )

