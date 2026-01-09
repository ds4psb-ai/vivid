"""Context Library API Endpoints.

Provides REST endpoints for managing user-injected context documents,
following the Expert Workflow pattern for AI knowledge grounding.

Endpoints:
- POST /context/documents - Add a context document
- GET /context/documents - List documents for session
- DELETE /context/documents/{id} - Remove a document
- POST /context/clear - Clear all session documents
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.routers.dimension._base import get_current_user
from app.rag.context_library import (
    ContextDocument,
    ContextLibrary,
    get_context_library,
)

router = APIRouter(prefix="/context", tags=["Context Library"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AddDocumentRequest(BaseModel):
    """Request to add a context document."""
    title: str = Field(..., min_length=1, max_length=200, description="Document title")
    content: str = Field(..., min_length=10, max_length=50000, description="Document content")
    source_type: str = Field(
        "user_research",
        description="Source type: wiki, article, user_research, style_guide, reference_song, character_info"
    )
    tags: List[str] = Field(default_factory=list, description="Optional tags for filtering")


class DocumentResponse(BaseModel):
    """Response for a single document."""
    id: str
    title: str
    source_type: str
    tags: List[str]
    content_preview: str
    created_at: float


class AddDocumentResponse(BaseModel):
    """Response after adding a document."""
    success: bool
    document_id: str
    message: str


class ListDocumentsResponse(BaseModel):
    """Response for listing documents."""
    documents: List[DocumentResponse]
    total: int


class ClearSessionResponse(BaseModel):
    """Response after clearing session."""
    success: bool
    documents_removed: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/documents",
    response_model=AddDocumentResponse,
    summary="Add Context Document",
    description="Add a context document (Wiki, article, research) to enhance AI understanding.",
)
async def add_document(
    request: AddDocumentRequest,
    user: dict = Depends(get_current_user),
) -> AddDocumentResponse:
    """Add a context document to the user's session.
    
    This follows the Expert Workflow pattern where users inject
    knowledge that the AI lacks (e.g., Wiki articles about a topic).
    """
    session_id = user.get("id", "anonymous")
    
    # Validate source type
    valid_types = {"wiki", "article", "user_research", "style_guide", "reference_song", "character_info"}
    if request.source_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Create document
    doc = ContextDocument(
        title=request.title,
        content=request.content,
        source_type=request.source_type,
        tags=request.tags[:10],  # Limit tags
    )
    
    # Add to library
    library = get_context_library()
    doc_id = library.add_document(session_id, doc)
    
    return AddDocumentResponse(
        success=True,
        document_id=doc_id,
        message=f"Document '{request.title}' added successfully.",
    )


@router.get(
    "/documents",
    response_model=ListDocumentsResponse,
    summary="List Context Documents",
    description="List all context documents for the current session.",
)
async def list_documents(
    source_type: Optional[str] = None,
    user: dict = Depends(get_current_user),
) -> ListDocumentsResponse:
    """List all context documents for the user's session."""
    session_id = user.get("id", "anonymous")
    
    library = get_context_library()
    docs = library.get_documents(session_id, source_type=source_type)
    
    return ListDocumentsResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                source_type=doc.source_type,
                tags=doc.tags,
                content_preview=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                created_at=doc.created_at,
            )
            for doc in docs
        ],
        total=len(docs),
    )


@router.delete(
    "/documents/{document_id}",
    response_model=AddDocumentResponse,
    summary="Remove Context Document",
    description="Remove a specific context document.",
)
async def remove_document(
    document_id: str,
    user: dict = Depends(get_current_user),
) -> AddDocumentResponse:
    """Remove a context document from the user's session."""
    session_id = user.get("id", "anonymous")
    
    library = get_context_library()
    removed = library.remove_document(session_id, document_id)
    
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found."
        )
    
    return AddDocumentResponse(
        success=True,
        document_id=document_id,
        message="Document removed successfully.",
    )


@router.post(
    "/clear",
    response_model=ClearSessionResponse,
    summary="Clear Session Context",
    description="Remove all context documents for the current session.",
)
async def clear_session(
    user: dict = Depends(get_current_user),
) -> ClearSessionResponse:
    """Clear all context documents for the user's session."""
    session_id = user.get("id", "anonymous")
    
    library = get_context_library()
    count = library.clear_session(session_id)
    
    return ClearSessionResponse(
        success=True,
        documents_removed=count,
    )
