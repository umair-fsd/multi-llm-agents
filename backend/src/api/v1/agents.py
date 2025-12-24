"""Agent API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from src.api.deps import CurrentUser, DbSession
from src.models.agent import Agent
from src.models.document import Document
from src.schemas.agent import (
    AgentCreate,
    AgentListResponse,
    AgentResponse,
    AgentUpdate,
    AgentCapabilities,
    ModelSettings,
    VoiceSettings,
)

router = APIRouter()


def agent_to_response(agent: Agent, doc_count: int = 0) -> AgentResponse:
    """Convert Agent model to response schema."""
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        model_settings=ModelSettings(**agent.model_settings) if agent.model_settings else ModelSettings(),
        capabilities=AgentCapabilities(**agent.capabilities) if agent.capabilities else AgentCapabilities(),
        voice_settings=VoiceSettings(**agent.voice_settings) if agent.voice_settings else VoiceSettings(),
        is_active=agent.is_active,
        is_default=agent.is_default,
        document_count=doc_count,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.get("", response_model=AgentListResponse)
async def list_agents(
    db: DbSession,
    user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
):
    """List all agents with pagination."""
    query = select(Agent)
    
    if is_active is not None:
        query = query.where(Agent.is_active == is_active)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    
    # Get paginated results
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Agent.created_at.desc())
    result = await db.execute(query)
    agents = result.scalars().all()
    
    # Get document counts for each agent
    items = []
    for agent in agents:
        doc_count_query = select(func.count()).where(Document.agent_id == agent.id)
        doc_count = await db.scalar(doc_count_query) or 0
        items.append(agent_to_response(agent, doc_count))
    
    return AgentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    db: DbSession,
    user: CurrentUser,
):
    """Create a new agent."""
    # If this agent is set as default, unset other defaults
    if data.is_default:
        await db.execute(
            Agent.__table__.update().values(is_default=False)
        )
    
    agent = Agent(
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        model_settings=data.model_settings.model_dump(),
        capabilities=data.capabilities.model_dump(),
        voice_settings=data.voice_settings.model_dump(),
        is_active=data.is_active,
        is_default=data.is_default,
    )
    
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    
    return agent_to_response(agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """Get a specific agent by ID."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    doc_count_query = select(func.count()).where(Document.agent_id == agent.id)
    doc_count = await db.scalar(doc_count_query) or 0
    
    return agent_to_response(agent, doc_count)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    data: AgentUpdate,
    db: DbSession,
    user: CurrentUser,
):
    """Update an existing agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # If setting as default, unset other defaults
    if data.is_default:
        await db.execute(
            Agent.__table__.update().where(Agent.id != agent_id).values(is_default=False)
        )
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field in ["model_settings", "capabilities", "voice_settings"]:
                setattr(agent, field, value.model_dump() if hasattr(value, "model_dump") else value)
            else:
                setattr(agent, field, value)
    
    await db.flush()
    await db.refresh(agent)
    
    doc_count_query = select(func.count()).where(Document.agent_id == agent.id)
    doc_count = await db.scalar(doc_count_query) or 0
    
    return agent_to_response(agent, doc_count)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """Delete an agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    await db.delete(agent)
    await db.flush()
