"""Document API endpoints."""

import hashlib
import os
import uuid as uuid_lib
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import func, select

from src.api.deps import CurrentUser, DbSession
from src.models.agent import Agent
from src.models.document import Document, DocumentStatus
from src.schemas.document import DocumentListResponse, DocumentResponse

router = APIRouter()

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


def document_to_response(doc: Document) -> DocumentResponse:
    """Convert Document model to response schema."""
    return DocumentResponse(
        id=doc.id,
        agent_id=doc.agent_id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        status=doc.status,
        error_message=doc.error_message,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
        processed_at=doc.processed_at,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    db: DbSession,
    user: CurrentUser,
    agent_id: UUID | None = None,
):
    """List all documents, optionally filtered by agent."""
    query = select(Document)
    
    if agent_id:
        query = query.where(Document.agent_id == agent_id)
    
    query = query.order_by(Document.created_at.desc())
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        items=[document_to_response(doc) for doc in documents],
        total=len(documents),
    )


@router.post("/upload/{agent_id}", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    agent_id: UUID,
    file: UploadFile = File(...),
    db: DbSession = None,
    user: CurrentUser = None,
):
    """Upload a document for an agent."""
    # Verify agent exists
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: PDF, TXT, DOCX",
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid_lib.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Calculate hash
    content_hash = hashlib.sha256(content).hexdigest()
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create document record
    document = Document(
        agent_id=agent_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
        content_hash=content_hash,
        status=DocumentStatus.PENDING.value,
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Process document for RAG in background
    import asyncio
    from src.services.rag_service import rag_service
    
    async def process_in_background():
        """Process document asynchronously."""
        from src.db.database import async_session_maker
        async with async_session_maker() as bg_db:
            try:
                await rag_service.process_document(
                    db=bg_db,
                    document_id=str(document.id),
                )
            except Exception as e:
                print(f"RAG processing error for {document.id}: {e}")
    
    # Start background processing
    asyncio.create_task(process_in_background())
    
    return document_to_response(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """Get a specific document by ID."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return document_to_response(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """Delete a document."""
    from src.services.rag_service import rag_service
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Delete file if exists
    file_path = Path(document.file_path)
    if file_path.exists():
        os.remove(file_path)
    
    # Delete from Qdrant
    try:
        await rag_service.delete_document_chunks(
            agent_id=str(document.agent_id),
            document_id=str(document_id),
        )
    except Exception as e:
        # Log but don't fail if Qdrant deletion fails
        print(f"Warning: Failed to delete from Qdrant: {e}")
    
    await db.delete(document)
    await db.flush()


@router.post("/{document_id}/process", response_model=DocumentResponse)
async def process_document(
    document_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """Trigger processing of a document for RAG."""
    from src.services.rag_service import rag_service
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    try:
        # Process document using RAG service
        await rag_service.process_document(
            db=db,
            document_id=str(document_id),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}",
        )
    
    await db.refresh(document)
    return document_to_response(document)
