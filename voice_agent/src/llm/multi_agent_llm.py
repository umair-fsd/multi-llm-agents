"""
MultiAgentLLM - Optimized wrapper with fast agent routing and smart tool execution.
"""

import logging
import re
from typing import Optional
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from livekit.agents import llm
from livekit.plugins import openai as openai_plugin

from src.tools.web_search import WebSearchTool
from src.tools.weather import WeatherTool
from src.tools.rag_retriever import RAGRetriever
from src.config import GROQ_API_KEY, DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL

logger = logging.getLogger(__name__)

# Keywords that trigger web search (for real-time info)
WEB_SEARCH_TRIGGERS = [
    'news', 'today', 'current', 'latest', 'recent',
    'price', 'stock', 'bitcoin', 'crypto',
    'who is', 'when did', 'what happened', 'what is',
    'prime minister', 'president', 'election',
    'who is the president', 'who is president',
]

# Keywords that trigger weather tool
WEATHER_TRIGGERS = [
    'weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy',
    'hot', 'cold', 'humid', 'wind', 'snow', 'storm',
]


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
    Optimized multi-agent LLM with fast routing and smart tool execution.
    Supports multiple LLM providers: openai, groq, openrouter.
    """
    
    def __init__(
        self,
        agents: list[dict],
        model: str = None,
        api_key: Optional[str] = None,
        provider: str = None,
    ):
        # Determine provider and configure
        self._provider = provider or DEFAULT_LLM_PROVIDER or "groq"
        self._use_groq = self._provider == "groq"
        self._use_openrouter = self._provider == "openrouter"
        
        # Configure base URL and model based on provider
        base_url = None
        if self._use_groq:
            model = model or DEFAULT_LLM_MODEL or "llama-3.1-70b-versatile"
            api_key = api_key or GROQ_API_KEY
            base_url = "https://api.groq.com/openai/v1"
            logger.info(f"🚀 Using Groq LLM: {model} (FREE tier)")
        elif self._use_openrouter:
            model = model or "anthropic/claude-3.5-sonnet"
            base_url = "https://openrouter.ai/api/v1"
            logger.info(f"🚀 Using OpenRouter LLM: {model}")
        else:
            model = model or "gpt-4o-mini"
            logger.info(f"Using OpenAI LLM: {model}")
        
        # Initialize parent with OpenAI plugin
        super().__init__(model=model, api_key=api_key, base_url=base_url)
        
        self.agents = agents
        
        # Fast routing using keyword matching (no API call needed)
        self._build_keyword_routing()
        
        self._current_agent: Optional[AgentContext] = None
        self._on_agent_switch_callbacks = []
        self._web_search_tool = None
        self._weather_tool = None
        self._rag_retrievers: dict[str, RAGRetriever] = {}  # Cache by agent_id
        self._last_tools_used: list[str] = []  # Track tools used in last call
        
        logger.info(f"MultiAgentLLM initialized with {len(agents)} agents (fast routing)")
    
    def _needs_weather(self, user_message: str) -> bool:
        """Check if query is asking about weather."""
        msg_lower = user_message.lower()
        return any(trigger in msg_lower for trigger in WEATHER_TRIGGERS)
    
    def _build_keyword_routing(self):
        """Build keyword-based routing using admin-defined keywords from capabilities."""
        self._agent_keywords = {}
        
        for agent in self.agents:
            capabilities = agent.get('capabilities', {})
            
            # Get admin-defined routing keywords
            keywords = set(capabilities.get('routing_keywords', []))
            
            # Auto-add weather keywords if weather capability is enabled
            if capabilities.get('weather', {}).get('enabled'):
                keywords.update(['weather', 'temperature', 'forecast'])
            
            self._agent_keywords[agent['name']] = keywords
            if keywords:
                logger.info(f"Agent '{agent['name']}' routing keywords: {keywords}")
        
        logger.info(f"Fast routing configured for {len(self.agents)} agents")
    
    def _fast_route(self, user_message: str) -> dict:
        """Fast keyword-based routing (no API call)."""
        msg_lower = user_message.lower()
        
        # Score each agent based on keyword matches
        scores = {}
        for agent in self.agents:
            keywords = self._agent_keywords.get(agent['name'], set())
            score = sum(1 for kw in keywords if kw in msg_lower)
            scores[agent['name']] = score
        
        # Find best match
        best_agent = max(self.agents, key=lambda a: scores.get(a['name'], 0))
        
        # If no keywords matched, use first agent
        if scores.get(best_agent['name'], 0) == 0:
            best_agent = self.agents[0]
        
        logger.info(f"⚡ Fast route: '{user_message[:30]}...' → {best_agent['name']}")
        return best_agent
    
    def _needs_web_search(self, user_message: str) -> bool:
        """Check if query needs web search (real-time info)."""
        msg_lower = user_message.lower()
        return any(trigger in msg_lower for trigger in WEB_SEARCH_TRIGGERS)
    
    @property
    def current_agent(self) -> Optional[AgentContext]:
        return self._current_agent
    
    def on_agent_switch(self, callback):
        self._on_agent_switch_callbacks.append(callback)
    
    def _get_latest_user_message(self, chat_ctx: llm.ChatContext) -> Optional[str]:
        for item in reversed(list(chat_ctx.items)):
            if hasattr(item, 'role') and item.role == "user":
                content = None
                if hasattr(item, 'text'):
                    content = item.text
                elif hasattr(item, 'content'):
                    content = item.content
                
                if content:
                    # Handle if content is a list (extract text)
                    if isinstance(content, list):
                        texts = []
                        for c in content:
                            if isinstance(c, str):
                                texts.append(c)
                            elif hasattr(c, 'text'):
                                texts.append(c.text)
                        return ' '.join(texts) if texts else None
                    return str(content)
        return None
    
    def _modify_chat_context(self, chat_ctx: llm.ChatContext, tool_context: Optional[str] = None) -> llm.ChatContext:
        """Add concise system prompt optimized for voice."""
        if not self._current_agent:
            return chat_ctx
        
        new_ctx = llm.ChatContext()
        
        # Build the system prompt - KEEP IT SHORT for speed
        if tool_context:
            # Short prompt with tool data
            prompt = f"""You are {self._current_agent.name}. Answer in 1 sentence.

USE THIS DATA (today's date: {__import__('datetime').date.today()}):
{tool_context[:500]}

Answer from the data above only."""
            logger.info(f"📝 Tool context added ({len(tool_context)} chars)")
        else:
            # Minimal prompt for speed
            prompt = f"{self._current_agent.name}: {self._current_agent.system_prompt[:200]}\nBe brief (1 sentence)."
        
        new_ctx.add_message(role="system", content=prompt)
        
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
        return MultiAgentStream(
            multi_agent_llm=self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            kwargs=kwargs,
        )


class MultiAgentStream(llm.LLMStream):
    """Optimized stream with fast routing and conditional web search."""
    
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
    
    async def _execute_web_search(self, query: str, capabilities: dict) -> Optional[str]:
        """Execute web search only if enabled and query needs it."""
        web_config = capabilities.get('web_search', {})
        if not web_config.get('enabled', False):
            return None
        
        # Only search if query needs real-time info
        if not self._multi_agent_llm._needs_web_search(query):
            return None
        
        try:
            # Get search provider from agent's capabilities (set in admin per agent)
            provider = web_config.get('provider', 'duckduckgo')
            max_results = web_config.get('max_results', 3)
            logger.info(f"🔍 Searching with {provider}: {query[:40]}...")
            
            # Recreate tool if provider changed
            if not self._multi_agent_llm._web_search_tool or \
               self._multi_agent_llm._web_search_tool.provider != provider:
                self._multi_agent_llm._web_search_tool = WebSearchTool(
                    provider=provider,
                    max_results=max_results
                )
            
            results = await self._multi_agent_llm._web_search_tool.search(query)
            
            if results and "error" not in results.lower():
                logger.info(f"✅ Search done - got {len(results)} chars")
                logger.info(f"📋 Search results preview: {results[:200]}...")
                # Track that web search was used
                self._multi_agent_llm._last_tools_used = ['web_search']
                return results[:800]  # Keep more context for better answers
            
        except Exception as e:
            logger.warning(f"Search failed: {e}")
        
        return None
    
    async def _execute_weather(self, query: str, capabilities: dict) -> Optional[str]:
        """Execute weather lookup if enabled and query asks for weather."""
        weather_config = capabilities.get('weather', {})
        if not weather_config.get('enabled', False):
            return None
        
        # Only get weather if query asks for it
        if not self._multi_agent_llm._needs_weather(query):
            return None
        
        try:
            units = weather_config.get('units', 'metric')
            logger.info(f"🌤️ Getting weather for: {query[:40]}...")
            
            # Create weather tool if needed
            if not self._multi_agent_llm._weather_tool:
                self._multi_agent_llm._weather_tool = WeatherTool()
            
            # Set units
            self._multi_agent_llm._weather_tool.units = units
            
            result = await self._multi_agent_llm._weather_tool.search(query)
            
            if result and "error" not in result.lower() and "Could not" not in result:
                logger.info(f"✅ Weather retrieved")
                self._multi_agent_llm._last_tools_used.append('weather')
                return result
            
        except Exception as e:
            logger.warning(f"Weather lookup failed: {e}")
        
        return None
    
    async def _execute_rag(self, query: str, capabilities: dict, agent_id: str) -> Optional[str]:
        """Execute RAG retrieval if enabled for this agent."""
        rag_config = capabilities.get('rag', {})
        if not rag_config.get('enabled', False):
            logger.info(f"📚 RAG not enabled for this agent")
            return None
        
        try:
            top_k = rag_config.get('top_k', 5)
            collection_name = f"agent_{agent_id.replace('-', '_')}_docs"
            logger.info(f"📚 RAG search for: {query[:40]}... (collection: {collection_name})")
            
            # Get or create RAG retriever for this agent
            if agent_id not in self._multi_agent_llm._rag_retrievers:
                self._multi_agent_llm._rag_retrievers[agent_id] = RAGRetriever(
                    collection_name=collection_name,
                    top_k=top_k
                )
            
            retriever = self._multi_agent_llm._rag_retrievers[agent_id]
            result = await retriever.search(query)
            logger.info(f"📚 RAG result: {result[:200] if result else 'None'}...")
            
            if result and "No documents found" not in result and "No relevant information" not in result and "error" not in result.lower():
                logger.info(f"✅ RAG retrieved {len(result)} chars")
                self._multi_agent_llm._last_tools_used.append('rag')
                return result
            else:
                logger.info(f"📚 RAG: No relevant docs found - result was: {result[:100] if result else 'None'}")
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}", exc_info=True)
        
        return None
    
    async def _run(self) -> None:
        """Optimized run with fast routing."""
        try:
            # Reset tools tracking for this call
            self._multi_agent_llm._last_tools_used = []
            
            user_message = self._multi_agent_llm._get_latest_user_message(self._chat_ctx)
            tool_context = None
            
            if user_message:
                # Fast keyword-based routing (no API call!)
                selected_agent = self._multi_agent_llm._fast_route(user_message)
                
                old_agent_name = (
                    self._multi_agent_llm._current_agent.name 
                    if self._multi_agent_llm._current_agent else None
                )
                
                self._multi_agent_llm._current_agent = AgentContext(
                    name=selected_agent['name'],
                    id=selected_agent['id'],
                    system_prompt=selected_agent['system_prompt'],
                    model_settings=selected_agent.get('model_settings', {}),
                    capabilities=selected_agent.get('capabilities', {}),
                )
                
                if old_agent_name and old_agent_name != selected_agent['name']:
                    logger.info(f"🔄 Switched: {old_agent_name} → {selected_agent['name']}")
                    # Call registered callbacks
                    for callback in self._multi_agent_llm._on_agent_switch_callbacks:
                        try:
                            callback(old_agent_name, selected_agent['name'])
                        except Exception as e:
                            logger.error(f"Agent switch callback error: {e}")
                
                # Execute tools in PARALLEL for speed
                import asyncio
                capabilities = self._multi_agent_llm._current_agent.capabilities
                agent_id = self._multi_agent_llm._current_agent.id
                
                # Determine which tools to run
                needs_rag = capabilities.get('rag', {}).get('enabled', False)
                needs_weather = capabilities.get('weather', {}).get('enabled', False) and self._multi_agent_llm._needs_weather(user_message)
                needs_search = capabilities.get('web_search', {}).get('enabled', False) and self._multi_agent_llm._needs_web_search(user_message) and not needs_weather
                
                # Run applicable tools in parallel
                tasks = []
                task_names = []
                
                if needs_rag:
                    tasks.append(self._execute_rag(user_message, capabilities, agent_id))
                    task_names.append('rag')
                if needs_weather:
                    tasks.append(self._execute_weather(user_message, capabilities))
                    task_names.append('weather')
                if needs_search:
                    tasks.append(self._execute_web_search(user_message, capabilities))
                    task_names.append('search')
                
                # Execute all tools concurrently
                tool_results = []
                if tasks:
                    logger.info(f"⚡ Running {len(tasks)} tools in parallel: {task_names}")
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for r in results:
                        if r and not isinstance(r, Exception):
                            tool_results.append(r)
                
                tool_context = "\n\n".join(tool_results) if tool_results else None
            
            # Build optimized context
            modified_ctx = self._multi_agent_llm._modify_chat_context(self._chat_ctx, tool_context)
            
            # Call parent LLM
            parent_stream = openai_plugin.LLM.chat(
                self._multi_agent_llm,
                chat_ctx=modified_ctx,
                tools=self._tools,
                **self._kwargs,
            )
            
            async with parent_stream as stream:
                async for chunk in stream:
                    self._event_ch.send_nowait(chunk)
                    
        except Exception as e:
            logger.error(f"Stream error: {e}")
            raise
    
    async def aclose(self) -> None:
        pass
