"""
Modular Provider System for Voice Agent.

This module provides pluggable TTS, STT, and LLM providers
that can be configured via the admin panel.
"""

from .tts import get_tts_provider, TTS_PROVIDERS
from .stt import get_stt_provider, STT_PROVIDERS
from .llm import get_llm_provider, LLM_PROVIDERS

__all__ = [
    "get_tts_provider",
    "get_stt_provider", 
    "get_llm_provider",
    "TTS_PROVIDERS",
    "STT_PROVIDERS",
    "LLM_PROVIDERS",
]

