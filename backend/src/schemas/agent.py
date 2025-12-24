"""Agent schemas - request/response models."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WebSearchConfig(BaseModel):
    """Web search capability configuration."""
    enabled: bool = False
    provider: Literal["tavily", "brave", "duckduckgo"] = "duckduckgo"
    max_results: int = Field(default=5, ge=1, le=20)


class WeatherConfig(BaseModel):
    """Weather capability configuration."""
    enabled: bool = False
    units: Literal["metric", "imperial"] = "metric"  # Celsius or Fahrenheit


class RAGConfig(BaseModel):
    """RAG capability configuration."""
    enabled: bool = False
    collection_name: str | None = None
    chunk_size: int = Field(default=1000, ge=100, le=4000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class ModelSettings(BaseModel):
    """LLM model configuration."""
    provider: Literal["openai", "openrouter"] = "openai"
    model_name: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


class VoiceSettings(BaseModel):
    """Voice/TTS configuration."""
    tts_voice: str = "aura-asteria-en"
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0)


class AgentCapabilities(BaseModel):
    """Agent capabilities configuration."""
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
    weather: WeatherConfig = Field(default_factory=WeatherConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    routing_keywords: list[str] = Field(default_factory=list, description="Keywords to route queries to this agent")
    tools: list[str] = Field(default_factory=list)


class AgentCreate(BaseModel):
    """Schema for creating a new agent."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    system_prompt: str = Field(..., min_length=1)
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings)
    is_active: bool = True
    is_default: bool = False


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    system_prompt: str | None = None
    model_settings: ModelSettings | None = None
    capabilities: AgentCapabilities | None = None
    voice_settings: VoiceSettings | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class AgentResponse(BaseModel):
    """Schema for agent response."""
    id: UUID
    name: str
    description: str | None
    system_prompt: str
    model_settings: ModelSettings
    capabilities: AgentCapabilities
    voice_settings: VoiceSettings
    is_active: bool
    is_default: bool
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Schema for list of agents."""
    items: list[AgentResponse]
    total: int
    page: int
    page_size: int
