"""
Large Language Model (LLM) Providers.

Supported providers:
- openai: OpenAI GPT models (paid)
- groq: Groq (FREE, very fast)
- openrouter: OpenRouter (access to many models)
"""

import logging
from typing import Optional

from livekit.agents import llm

logger = logging.getLogger(__name__)

# Registry of available LLM providers
LLM_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "description": "GPT-4o, GPT-4, GPT-3.5 Turbo",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "requires_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "groq": {
        "name": "Groq (FREE)",
        "description": "Ultra-fast inference, free tier available",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-groq-70b-8192-tool-use-preview", "mixtral-8x7b-32768"],
        "requires_key": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "name": "OpenRouter",
        "description": "Access to Claude, Gemini, Llama, and more",
        "models": ["anthropic/claude-3.5-sonnet", "google/gemini-pro", "meta-llama/llama-3.1-70b-instruct"],
        "requires_key": "OPENROUTER_API_KEY",
        "default_model": "anthropic/claude-3.5-sonnet",
    },
}


def get_llm_provider(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
) -> Optional[llm.LLM]:
    """
    Get an LLM provider instance.
    
    Args:
        provider: Provider name (openai, groq, openrouter)
        model: Model name to use
        api_key: Optional API key override
        temperature: Sampling temperature
        
    Returns:
        LLM instance or None if provider unavailable
    """
    try:
        if provider == "openai":
            from .openai_llm import create_openai_llm
            return create_openai_llm(model=model, api_key=api_key, temperature=temperature)
            
        elif provider == "groq":
            from .groq_llm import create_groq_llm
            return create_groq_llm(model=model, api_key=api_key, temperature=temperature)
            
        elif provider == "openrouter":
            from .openrouter_llm import create_openrouter_llm
            return create_openrouter_llm(model=model, api_key=api_key, temperature=temperature)
            
        else:
            logger.error(f"Unknown LLM provider: {provider}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create LLM provider '{provider}': {e}")
        return None

