"""Configuration for voice agent service."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment
load_dotenv()

# LiveKit Configuration
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret_min_32_chars_for_development")

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "groq")  # Default to Groq (free)
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "llama-3.1-70b-versatile")  # Groq model

# Speech Services (Deepgram)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")

# TTS Providers
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
DEFAULT_TTS_PROVIDER = os.getenv("DEFAULT_TTS_PROVIDER", "openai")  # openai, elevenlabs, or none

# Web Search
def _get_tavily_key():
    """Get Tavily API key from various sources."""
    key = os.getenv("TAVILY_API_KEY", "")
    # Skip placeholder values
    if key and "your-" not in key and "xxx" not in key.lower():
        return key
    # Try extracting from MCP link
    mcp_link = os.getenv("TAVILY_MCP_LINK", "")
    if "tavilyApiKey=" in mcp_link:
        return mcp_link.split("tavilyApiKey=")[1].split("&")[0]
    return ""

TAVILY_API_KEY = _get_tavily_key()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
DEFAULT_SEARCH_PROVIDER = os.getenv("DEFAULT_SEARCH_PROVIDER", "duckduckgo")

# Weather
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "") or os.getenv("OPEN_WEATHER_MAP_API", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/agentic_ai")

# Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
