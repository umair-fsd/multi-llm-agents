"""RAG document processing service."""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.document import Document, DocumentStatus


class RAGService:
    """Service for processing documents for RAG."""

    def __init__(self):
        self.qdrant = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)

    def get_collection_name(self, agent_id: str) -> str:
        """Get the Qdrant collection name for an agent."""
        # Replace hyphens with underscores for valid collection name
        return f"agent_{agent_id.replace('-', '_')}_docs"

    async def ensure_collection_exists(self, collection_name: str):
        """Create collection if it doesn't exist."""
        collections = await self.qdrant.get_collections()
        collection_names = [c.name for c in collections.collections]

        if collection_name not in collection_names:
            # Create collection with vector params
            # OpenAI embeddings are 1536 dimensions
            await self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1536,
                    distance=Distance.COSINE,
                ),
            )

    async def process_pdf(self, file_path: Path) -> list[str]:
        """
        Extract text from PDF and split into chunks.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of text chunks
        """
        # Load PDF
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()

        # Combine all pages
        full_text = "\n\n".join([page.page_content for page in pages])

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        chunks = text_splitter.split_text(full_text)
        return chunks

    async def process_text_file(self, file_path: Path) -> list[str]:
        """
        Extract text from text file and split into chunks.
        
        Args:
            file_path: Path to text file
            
        Returns:
            List of text chunks
        """
        loader = TextLoader(str(file_path))
        docs = loader.load()

        # Combine all documents
        full_text = "\n\n".join([doc.page_content for doc in docs])

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        chunks = text_splitter.split_text(full_text)
        return chunks

    async def embed_and_store(
        self,
        chunks: list[str],
        collection_name: str,
        document_id: str,
        source_filename: str,
    ):
        """
        Embed chunks and store in Qdrant.
        
        Args:
            chunks: List of text chunks
            collection_name: Qdrant collection name
            document_id: Document UUID
            source_filename: Original filename for metadata
        """
        # Ensure collection exists
        await self.ensure_collection_exists(collection_name)

        # Embed all chunks
        embeddings = await self.embeddings.aembed_documents(chunks)

        # Create points for Qdrant
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": chunk,
                    "document_id": document_id,
                    "source": source_filename,
                    "chunk_index": idx,
                },
            )
            points.append(point)

        # Upload to Qdrant
        await self.qdrant.upsert(
            collection_name=collection_name,
            points=points,
        )

    async def process_document(
        self,
        db: AsyncSession,
        document_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Process a document: chunk, embed, and store in Qdrant.
        
        Args:
            db: Database session
            document_id: UUID of document to process
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        # Get document from database
        result = await db.execute(
            select(Document).where(Document.id == uuid.UUID(document_id))
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        try:
            # Update status to processing
            document.status = DocumentStatus.PROCESSING.value
            await db.commit()

            file_path = Path(document.file_path)

            # Extract and chunk text based on file type
            if document.mime_type == "application/pdf":
                chunks = await self.process_pdf(file_path)
            elif document.mime_type == "text/plain":
                chunks = await self.process_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {document.mime_type}")

            # Get collection name from agent
            collection_name = self.get_collection_name(str(document.agent_id))

            # Embed and store
            await self.embed_and_store(
                chunks=chunks,
                collection_name=collection_name,
                document_id=str(document.id),
                source_filename=document.original_filename,
            )

            # Update document status
            document.status = DocumentStatus.COMPLETED.value
            document.chunk_count = len(chunks)
            document.processed_at = datetime.utcnow()
            await db.commit()

        except Exception as e:
            # Update status to failed
            document.status = DocumentStatus.FAILED.value
            document.error_message = str(e)
            await db.commit()
            raise

    async def delete_document_chunks(self, agent_id: str, document_id: str):
        """
        Delete all chunks for a document from Qdrant.
        
        Args:
            agent_id: Agent UUID
            document_id: Document UUID
        """
        collection_name = self.get_collection_name(agent_id)

        # Check if collection exists
        collections = await self.qdrant.get_collections()
        collection_names = [c.name for c in collections.collections]

        if collection_name in collection_names:
            # Delete points with this document_id
            await self.qdrant.delete(
                collection_name=collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {
                                "key": "document_id",
                                "match": {"value": document_id},
                            }
                        ]
                    }
                },
            )


# Create singleton instance
rag_service = RAGService()
