"""API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db


# Database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


# Dummy auth dependency for now
async def get_current_user():
    """Dummy auth - returns a fake admin user."""
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "admin@example.com",
        "name": "Admin User",
        "is_admin": True,
    }


CurrentUser = Annotated[dict, Depends(get_current_user)]
