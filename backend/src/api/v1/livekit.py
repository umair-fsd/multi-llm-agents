"""LiveKit API endpoints for token generation."""

from fastapi import APIRouter, HTTPException
from livekit.api import AccessToken, VideoGrants

from src.config import settings

router = APIRouter()


@router.get("/token")
async def create_livekit_token(room: str, identity: str):
    """
    Generate a LiveKit access token for a user to join a room.
    
    Args:
        room: Room name
        identity: User identity/name
        
    Returns:
        Access token for LiveKit room
    """
    try:
        token = (
            AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
            .with_identity(identity)
            .with_name(identity)
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=room,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .to_jwt()
        )

        return {"token": token}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create token: {str(e)}")
