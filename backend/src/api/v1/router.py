"""API v1 router - aggregates all routes."""

from fastapi import APIRouter

from src.api.v1 import agents, documents, sessions, settings, livekit

api_router = APIRouter()

api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(livekit.router, prefix="/livekit", tags=["LiveKit"])
