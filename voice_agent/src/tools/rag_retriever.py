"""RAG retriever tool for document Q&A."""

import logging
from langchain_openai import OpenAIEmbeddings
from qdrant_client import AsyncQdrantClient

from src.config import QDRANT_HOST, QDRANT_PORT, OPENAI_API_KEY

logger = logging.getLogger(__name__)


class RAGRetriever:
    """RAG retrieval tool for querying document collections."""

    def __init__(self, collection_name: str, top_k: int = 5):
        self.collection_name = collection_name
        self.top_k = top_k
        self.client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        logger.info(f"📚 RAGRetriever created for collection: {collection_name} (host: {QDRANT_HOST}:{QDRANT_PORT})")

    async def search(self, query: str) -> str:
        """
        Search the document collection for relevant context.
        
        Args:
            query: The user's question
            
        Returns:
            Formatted string with relevant document chunks
        """
        try:
            # Get collections
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            logger.info(f"📚 Available Qdrant collections: {collection_names}")
            
            if self.collection_name not in collection_names:
                logger.warning(f"📚 Collection '{self.collection_name}' not found!")
                return f"No documents found in collection: {self.collection_name}"

            # Embed the query
            logger.info(f"📚 Embedding query: {query[:50]}...")
            query_vector = await self.embeddings.aembed_query(query)

            # Search for similar chunks using query_points
            from qdrant_client.models import models
            results = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=self.top_k,
            )
            points = results.points if hasattr(results, 'points') else results
            logger.info(f"📚 Qdrant search returned {len(points)} results")

            if not points:
                return "No relevant information found in the documents."

            # Format results
            formatted = f"Relevant information from documents:\n\n"
            for idx, hit in enumerate(points, 1):
                content = hit.payload.get("text", "")
                source = hit.payload.get("source", "Unknown")
                score = getattr(hit, 'score', 0)
                logger.info(f"📚 Result {idx}: score={score:.3f}, source={source}, content={content[:100]}...")
                formatted += f"{idx}. (Source: {source})\n{content}\n\n"

            return formatted

        except Exception as e:
            logger.error(f"📚 RAG search error: {e}")
            return f"RAG retrieval error: {str(e)}"


async def create_rag_retriever(agent_id: str, top_k: int = 5) -> RAGRetriever:
    """
    Create a RAG retriever for a specific agent.
    
    Args:
        agent_id: The UUID of the agent
        top_k: Number of chunks to retrieve
        
    Returns:
        Configured RAG retriever
    """
    collection_name = f"agent_{agent_id.replace('-', '_')}_docs"
    return RAGRetriever(collection_name=collection_name, top_k=top_k)
