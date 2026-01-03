"""
RAG Router - Vector search and recommendation endpoints

Provides:
- POST /rag/search - Search similar tools
- GET /rag/recommend - Personalized recommendations
- POST /rag/reindex - Admin: reindex all tools
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models_telemetry import ToolManifest
from app.dependencies import get_current_user, require_admin
from app.services.vector_service import get_vector_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])


# === Request/Response Models ===

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(10, ge=1, le=50, description="Maximum results")
    category: Optional[str] = Field(None, description="Filter by category")
    min_tier: Optional[str] = Field(None, description="Minimum tier: experimental, verified, certified")


class ToolResult(BaseModel):
    id: str
    tool_key: Optional[str]
    display_name: Optional[str]
    description: Optional[str]
    category: Optional[str]
    tier: Optional[str]
    score: float


class SearchResponse(BaseModel):
    results: List[ToolResult]
    count: int


class RecommendResponse(BaseModel):
    recommendations: List[ToolResult]
    based_on: List[str]  # Tool IDs used for recommendation


class ReindexResponse(BaseModel):
    indexed_count: int
    message: str


# === Endpoints ===

@router.post("/search", response_model=SearchResponse)
async def search_tools(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search for similar tools using vector similarity.
    
    Example:
        POST /rag/search
        {"query": "resize image", "limit": 5}
    """
    service = get_vector_service()
    
    results = service.search(
        query=request.query,
        limit=request.limit,
        category=request.category,
        min_tier=request.min_tier,
    )
    
    return SearchResponse(
        results=[ToolResult(**r) for r in results],
        count=len(results),
    )


@router.get("/recommend", response_model=RecommendResponse)
async def get_recommendations(
    recent_tools: str = Query(..., description="Comma-separated recent tool IDs"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """
    Get personalized tool recommendations based on recent usage.
    
    Example:
        GET /rag/recommend?recent_tools=tool-1,tool-2&limit=5
    """
    tool_ids = [t.strip() for t in recent_tools.split(",") if t.strip()]
    
    if not tool_ids:
        raise HTTPException(status_code=400, detail="No tool IDs provided")
    
    service = get_vector_service()
    recommendations = service.get_recommendations(
        recent_tool_ids=tool_ids,
        limit=limit,
    )
    
    return RecommendResponse(
        recommendations=[ToolResult(**r) for r in recommendations],
        based_on=tool_ids[:5],
    )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_all_tools(
    user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Reindex all tools in the vector database.
    Admin only.
    """
    # Fetch all tools from database
    result = await db.execute(select(ToolManifest))
    tools = result.scalars().all()
    
    # Convert to dicts
    tool_dicts = [
        {
            "id": str(t.id),
            "tool_key": t.tool_key,
            "display_name": t.display_name,
            "description": t.description,
            "category": t.category,
            "tier": t.tier,
            "usage_count": t.usage_count,
            "quality_rating": t.quality_rating,
            "input_schema": t.input_schema,
        }
        for t in tools
    ]
    
    service = get_vector_service()
    count = service.reindex_all(tool_dicts)
    
    logger.info(f"Reindexed {count} tools by admin {user.get('email')}")
    
    return ReindexResponse(
        indexed_count=count,
        message=f"Successfully reindexed {count} tools",
    )


@router.get("/health")
async def rag_health():
    """Check RAG/Qdrant health."""
    try:
        service = get_vector_service()
        service.ensure_collection()
        return {"status": "healthy", "collection": "vivid_tools"}
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"RAG unhealthy: {e}")
