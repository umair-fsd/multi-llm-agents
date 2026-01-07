"""OpenRouter LLM Provider."""

import os
import logging
from typing import Optional

from livekit.plugins import openai

logger = logging.getLogger(__name__)


def create_openrouter_llm(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
) -> openai.LLM:
    """
    Create an OpenRouter LLM instance.
    
    OpenRouter provides access to Claude, Gemini, Llama, and many other models.
    
    Args:
        model: Model to use (anthropic/claude-3.5-sonnet, etc.)
        api_key: Optional API key override
        temperature: Sampling temperature
        
    Returns:
        LLM instance configured for OpenRouter
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    
    if not key:
        raise ValueError("OPENROUTER_API_KEY not configured")
    
    model = model or "anthropic/claude-3.5-sonnet"
    
    logger.info(f"Creating OpenRouter LLM with model: {model}")
    
    # OpenRouter uses OpenAI-compatible API
    return openai.LLM(
        model=model,
        api_key=key,
        base_url="https://openrouter.ai/api/v1",
        temperature=temperature,
    )

