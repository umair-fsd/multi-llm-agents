"""
Orchestrator for intelligent agent routing based on user intent.

Routes each query to the most appropriate specialist agent by analyzing
the user message and optionally recent conversation history.
"""

import logging
from typing import Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Routes user queries to the most appropriate specialist agent.
    
    Uses an LLM to classify user intent and match against available agents,
    considering both the current query and recent conversation context.
    """
    
    def __init__(self, agents: list[dict], openai_client: AsyncOpenAI):
        """
        Initialize orchestrator with available agents.
        
        Args:
            agents: List of agent configs from database
            openai_client: OpenAI client for classification
        """
        self.agents = agents
        self.client = openai_client
        self._build_agent_descriptions()
    
    def _format_capabilities(self, capabilities: dict) -> str:
        """Format agent capabilities into a readable string."""
        if not capabilities:
            return "None"
        
        caps = []
        if capabilities.get('web_search', {}).get('enabled'):
            caps.append("web search")
        if capabilities.get('rag', {}).get('enabled'):
            caps.append("document knowledge base")
        if capabilities.get('tools'):
            caps.extend([t.get('name', 'custom tool') for t in capabilities.get('tools', [])])
        
        return ", ".join(caps) if caps else "general conversation"
    
    def _build_agent_descriptions(self):
        """Build a formatted string of agent descriptions for the router."""
        self.agent_list = "\n".join([
            f"- {agent['name']}: {agent['description'] or 'General assistant'}. "
            f"Capabilities: {self._format_capabilities(agent.get('capabilities', {}))}"
            for agent in self.agents
        ])
        
        self.agent_names = [agent['name'] for agent in self.agents]
        
        logger.info(f"Orchestrator initialized with {len(self.agents)} agents: {self.agent_names}")
    
    def _format_history(self, history: list) -> str:
        """Format recent conversation history for context."""
        if not history:
            return ""
        
        formatted = "\nRecent conversation:\n"
        for item in history[-5:]:  # Last 5 messages
            role = item.get('role', 'unknown')
            content = item.get('content', '')[:100]  # Truncate long messages
            formatted += f"- {role}: {content}\n"
        
        return formatted
    
    async def route(
        self, 
        user_message: str, 
        conversation_history: list = None
    ) -> dict:
        """
        Route a user message to the most appropriate agent.
        
        Args:
            user_message: The user's query
            conversation_history: Recent conversation messages for context
            
        Returns:
            The selected agent config dict
        """
        if len(self.agents) == 1:
            return self.agents[0]
        
        if len(self.agents) == 0:
            return None
        
        # Format history for context
        history_context = self._format_history(conversation_history)
        
        # Build routing prompt with context
        routing_prompt = f"""You are an intelligent router that directs user queries to the most appropriate specialist agent.

Available Agents:
{self.agent_list}
{history_context}
Current User Query: "{user_message}"

Analyze the query (and conversation context if provided) and respond with ONLY the name of the best agent to handle this query.

Consider:
- What expertise or capabilities are needed?
- Does the query continue a previous topic? If so, use the same agent.
- Does the query match any agent's specialization or capabilities?
- If unclear, choose the most general agent.

Respond with just the agent name, nothing else."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": routing_prompt}],
                max_tokens=50,
                temperature=0,
            )
            
            selected_name = response.choices[0].message.content.strip()
            
            # Find matching agent (exact match first)
            for agent in self.agents:
                if agent['name'].lower() == selected_name.lower():
                    logger.info(f"Routed to: {agent['name']}")
                    return agent
            
            # Fuzzy match if exact match fails
            for agent in self.agents:
                if selected_name.lower() in agent['name'].lower() or \
                   agent['name'].lower() in selected_name.lower():
                    logger.info(f"Fuzzy matched to: {agent['name']}")
                    return agent
            
            # Fallback to first agent
            logger.warning(f"No match for '{selected_name}', using: {self.agents[0]['name']}")
            return self.agents[0]
            
        except Exception as e:
            logger.error(f"Routing error: {e}, using default agent")
            return self.agents[0]
    
    def get_agent_by_name(self, name: str) -> Optional[dict]:
        """Get an agent by name."""
        for agent in self.agents:
            if agent['name'].lower() == name.lower():
                return agent
        return None
    
    def get_default_agent(self) -> Optional[dict]:
        """Get the default/first agent."""
        return self.agents[0] if self.agents else None
