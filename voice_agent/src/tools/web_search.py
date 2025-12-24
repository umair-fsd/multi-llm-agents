"""Web search tool supporting multiple providers."""

import asyncio
import json
from typing import Any, Literal

import httpx
from duckduckgo_search import DDGS

from src.config import BRAVE_API_KEY, DEFAULT_SEARCH_PROVIDER, TAVILY_API_KEY


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
        """Search using Tavily API (optimized for AI)."""
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": self.max_results,
                    "include_answer": True,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            return [
                {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                }
                for result in data.get("results", [])
            ]

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
        """Search using DuckDuckGo (free, no API key needed)."""

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

        # Run in executor since DDGS is synchronous
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _search)

    async def search(self, query: str) -> str:
        """
        Search the web and return formatted results.
        
        Args:
            query: The search query
            
        Returns:
            Formatted string with search results
        """
        try:
            if self.provider == "tavily":
                results = await self.search_tavily(query)
            elif self.provider == "brave":
                results = await self.search_brave(query)
            else:  # duckduckgo
                results = await self.search_duckduckgo(query)

            if not results:
                return f"No search results found for: {query}"

            # Format results for LLM
            formatted = f"Search results for '{query}':\n\n"
            for idx, result in enumerate(results, 1):
                formatted += f"{idx}. {result['title']}\n"
                formatted += f"   URL: {result['url']}\n"
                formatted += f"   {result['content'][:200]}...\n\n"

            return formatted

        except Exception as e:
            return f"Search error: {str(e)}"


# Create a singleton instance
web_search = WebSearchTool()
