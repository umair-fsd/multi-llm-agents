"""Web search tool supporting multiple providers."""

import asyncio
import json
import logging
from typing import Any, Literal

import httpx

from src.config import BRAVE_API_KEY, DEFAULT_SEARCH_PROVIDER, TAVILY_API_KEY

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Multi-provider web search tool."""

    def __init__(
        self,
        provider: Literal["tavily", "brave", "duckduckgo"] = None,
        max_results: int = 5,
    ):
        self.provider = provider or DEFAULT_SEARCH_PROVIDER
        self.max_results = max_results

    async def search_tavily(self, query: str) -> list[dict[str, Any]]:
        """Search using Tavily API (optimized for AI with direct answers)."""
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY not configured")

        logger.info(f"🔍 Using Tavily API for: {query}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": self.max_results,
                    "include_answer": True,
                    "search_depth": "basic",  # Faster
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Tavily provides a direct AI-generated answer - use it first!
            if data.get("answer"):
                results.append({
                    "title": "Direct Answer",
                    "url": "",
                    "content": data["answer"],
                })
                logger.info(f"✅ Tavily direct answer: {data['answer'][:100]}...")

            # Add search results
            for result in data.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                })
            
            return results

    async def search_brave(self, query: str) -> list[dict[str, Any]]:
        """Search using Brave Search API."""
        if not BRAVE_API_KEY:
            raise ValueError("BRAVE_API_KEY not configured")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": BRAVE_API_KEY},
                params={"q": query, "count": self.max_results},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            return [
                {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("description", ""),
                }
                for result in data.get("web", {}).get("results", [])
            ]

    async def search_duckduckgo(self, query: str) -> list[dict[str, Any]]:
        """Search using DuckDuckGo via ddgs library or fallback to direct API."""
        
        # Try using ddgs library first
        try:
            from ddgs import DDGS
            
            def _search():
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=self.max_results))
                    return [
                        {
                            "title": result.get("title", ""),
                            "url": result.get("href", ""),
                            "content": result.get("body", ""),
                        }
                        for result in results
                    ]

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _search)
            if results:
                return results
        except ImportError:
            logger.warning("ddgs package not found, trying duckduckgo_search")
        except Exception as e:
            logger.warning(f"ddgs search failed: {e}")
        
        # Fallback: try duckduckgo_search
        try:
            from duckduckgo_search import DDGS as OldDDGS
            
            def _search_old():
                with OldDDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=self.max_results))
                    return [
                        {
                            "title": result.get("title", ""),
                            "url": result.get("href", ""),
                            "content": result.get("body", ""),
                        }
                        for result in results
                    ]

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _search_old)
            if results:
                return results
        except Exception as e:
            logger.warning(f"duckduckgo_search failed: {e}")
        
        # Final fallback: Direct DuckDuckGo HTML API (instant answers)
        try:
            async with httpx.AsyncClient() as client:
                # Use DuckDuckGo instant answer API
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                    },
                    timeout=10.0,
                    follow_redirects=True,
                )
                data = response.json()
                
                results = []
                
                # Get abstract (main answer)
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading", "Answer"),
                        "url": data.get("AbstractURL", ""),
                        "content": data.get("AbstractText", ""),
                    })
                
                # Get related topics
                for topic in data.get("RelatedTopics", [])[:self.max_results - len(results)]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " ") if topic.get("FirstURL") else "",
                            "url": topic.get("FirstURL", ""),
                            "content": topic.get("Text", ""),
                        })
                
                if results:
                    return results
                    
        except Exception as e:
            logger.error(f"DuckDuckGo instant answer API failed: {e}")
        
        return []

    async def search(self, query: str) -> str:
        """
        Search the web and return formatted results.
        
        Args:
            query: The search query
            
        Returns:
            Formatted string with search results
        """
        try:
            logger.info(f"🔍 Web search starting for: {query}")
            
            if self.provider == "tavily":
                results = await self.search_tavily(query)
            elif self.provider == "brave":
                results = await self.search_brave(query)
            else:  # duckduckgo
                results = await self.search_duckduckgo(query)

            if not results:
                logger.warning(f"No search results found for: {query}")
                return f"No search results found for: {query}"

            # Format results for LLM
            formatted = f"Web search results for '{query}':\n\n"
            for idx, result in enumerate(results, 1):
                formatted += f"{idx}. {result['title']}\n"
                if result['url']:
                    formatted += f"   Source: {result['url']}\n"
                formatted += f"   {result['content'][:300]}\n\n"

            logger.info(f"✅ Found {len(results)} search results")
            return formatted

        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Search error: {str(e)}"


# Create a singleton instance
web_search = WebSearchTool()
