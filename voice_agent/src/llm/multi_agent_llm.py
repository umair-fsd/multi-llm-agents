"""
MultiAgentLLM - Wrapper around OpenAI LLM with dynamic agent routing.

This provides multi-agent support by:
1. Using an orchestrator to select the best agent for each query
2. Modifying the chat context to include the selected agent's system prompt
3. Delegating the actual LLM call to the standard OpenAI plugin
"""

import logging
from typing import Optional
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from livekit.agents import llm
from livekit.plugins import openai as openai_plugin

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Tracks which agent is currently active."""
    name: str
    id: str
    system_prompt: str
    model_settings: dict = field(default_factory=dict)
    capabilities: dict = field(default_factory=dict)


class MultiAgentLLM(openai_plugin.LLM):
    """
    A wrapper around OpenAI LLM that adds dynamic agent routing.
    
    Inherits from the OpenAI plugin's LLM class and adds orchestration
    logic to select the best agent for each query.
    """
    
    def __init__(
        self,
        agents: list[dict],
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
    ):
        """
        Initialize MultiAgentLLM with available agents.
        
        Args:
            agents: List of agent configurations from database
            model: Default model to use
            api_key: OpenAI API key
        """
        # Initialize parent OpenAI LLM
        super().__init__(model=model, api_key=api_key)
        
        self.agents = agents
        self._async_client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()
        
        # Create orchestrator
        from .orchestrator import Orchestrator
        self.orchestrator = Orchestrator(agents, self._async_client)
        
        self._current_agent: Optional[AgentContext] = None
        self._on_agent_switch_callbacks = []
        
        logger.info(f"MultiAgentLLM initialized with {len(agents)} agents")
    
    @property
    def current_agent(self) -> Optional[AgentContext]:
        """Get the currently active agent context."""
        return self._current_agent
    
    def on_agent_switch(self, callback):
        """Register a callback for when the active agent changes."""
        self._on_agent_switch_callbacks.append(callback)
    
    async def _select_agent(self, user_message: str, chat_ctx: llm.ChatContext) -> Optional[dict]:
        """Select the best agent for the user's query."""
        # Get recent history for context
        history = []
        for item in list(chat_ctx.items)[-5:]:
            role = getattr(item, 'role', None)
            content = getattr(item, 'text', None) or getattr(item, 'content', None)
            if role and content:
                history.append({"role": role, "content": str(content)})
        
        return await self.orchestrator.route(user_message, conversation_history=history)
    
    def _get_latest_user_message(self, chat_ctx: llm.ChatContext) -> Optional[str]:
        """Extract the latest user message from chat context."""
        for item in reversed(list(chat_ctx.items)):
            if hasattr(item, 'role') and item.role == "user":
                if hasattr(item, 'text'):
                    return item.text
                if hasattr(item, 'content'):
                    return str(item.content)
        return None
    
    def _modify_chat_context(self, chat_ctx: llm.ChatContext) -> llm.ChatContext:
        """Add the selected agent's system prompt to the chat context."""
        if not self._current_agent:
            return chat_ctx
        
        # Create new chat context with agent's system prompt
        new_ctx = llm.ChatContext()
        
        # Add agent's system prompt first
        system_prompt = f"""You are {self._current_agent.name}.

{self._current_agent.system_prompt}

Important: You are a voice assistant. Keep responses concise (1-3 sentences) and natural for spoken conversation. Avoid bullet points, lists, or complex formatting."""
        
        new_ctx.add_message(role="system", content=system_prompt)
        
        # Copy existing messages (skip any existing system messages)
        for item in chat_ctx.items:
            role = getattr(item, 'role', None)
            if role and role != "system":
                content = getattr(item, 'text', None) or getattr(item, 'content', None)
                if content:
                    new_ctx.add_message(role=role, content=str(content))
        
        return new_ctx
    
    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list = None,
        **kwargs,
    ) -> "MultiAgentStream":
        """
        Process a chat request with dynamic agent routing.
        
        Returns a stream that will:
        1. Select the best agent for the query
        2. Modify the chat context with the agent's system prompt
        3. Delegate to the parent OpenAI LLM for actual inference
        """
        return MultiAgentStream(
            multi_agent_llm=self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            kwargs=kwargs,
        )


class MultiAgentStream(llm.LLMStream):
    """
    Stream wrapper that handles agent selection before delegating to OpenAI.
    """
    
    def __init__(
        self,
        multi_agent_llm: MultiAgentLLM,
        chat_ctx: llm.ChatContext,
        tools: list,
        kwargs: dict,
    ):
        from livekit.agents.types import APIConnectOptions
        
        super().__init__(
            llm=multi_agent_llm,
            chat_ctx=chat_ctx,
            tools=tools,
            conn_options=APIConnectOptions(),
        )
        self._multi_agent_llm = multi_agent_llm
        self._chat_ctx = chat_ctx
        self._tools = tools
        self._kwargs = kwargs
        self._inner_stream = None
    
    async def _run(self) -> None:
        """Run the stream with agent selection."""
        try:
            # Get the user's message
            user_message = self._multi_agent_llm._get_latest_user_message(self._chat_ctx)
            
            if user_message:
                # Select the best agent
                selected_agent = await self._multi_agent_llm._select_agent(
                    user_message, self._chat_ctx
                )
                
                if selected_agent:
                    old_agent_name = (
                        self._multi_agent_llm._current_agent.name 
                        if self._multi_agent_llm._current_agent else None
                    )
                    
                    # Update current agent
                    self._multi_agent_llm._current_agent = AgentContext(
                        name=selected_agent['name'],
                        id=selected_agent['id'],
                        system_prompt=selected_agent['system_prompt'],
                        model_settings=selected_agent.get('model_settings', {}),
                        capabilities=selected_agent.get('capabilities', {}),
                    )
                    
                    # Notify callbacks if agent switched
                    if old_agent_name and old_agent_name != selected_agent['name']:
                        logger.info(f"🔄 Agent switched: {old_agent_name} → {selected_agent['name']}")
                        for callback in self._multi_agent_llm._on_agent_switch_callbacks:
                            try:
                                import asyncio
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(old_agent_name, selected_agent['name'])
                                else:
                                    callback(old_agent_name, selected_agent['name'])
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
            
            # Modify chat context with agent's system prompt
            modified_ctx = self._multi_agent_llm._modify_chat_context(self._chat_ctx)
            
            # Call parent's chat method to get the actual stream
            # We need to use the parent class's implementation directly
            parent_stream = openai_plugin.LLM.chat(
                self._multi_agent_llm,
                chat_ctx=modified_ctx,
                tools=self._tools,
                **self._kwargs,
            )
            
            # Forward chunks from the parent stream
            async with parent_stream as stream:
                async for chunk in stream:
                    self._event_ch.send_nowait(chunk)
                    
        except Exception as e:
            logger.error(f"MultiAgentStream error: {e}")
            raise
    
    async def aclose(self) -> None:
        """Close the stream."""
        if self._inner_stream:
            await self._inner_stream.aclose()
