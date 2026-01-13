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


# === P1.6: Suggestion Endpoint ===

class EvidenceRefResponse(BaseModel):
    """Evidence reference for suggestion."""
    ref_id: str
    source: str = "db"
    content_preview: str = ""
    dataset_id: str = ""
    dataset_label: str = ""
    score: float = 0.0


class PromptChipResponse(BaseModel):
    """Quick insert chip."""
    label: str
    insert_text: str
    chip_type: str = "keyword"


class SuggestRequest(BaseModel):
    """P1.6: RAG suggestion request."""
    app_key: str = Field(..., description="App identifier (e.g., 'dimension.persona.analyze')")
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    history_context: Optional[str] = Field(None, description="Previous conversation context")
    inputs: Optional[Dict[str, Any]] = Field(None, description="Additional inputs")


class SuggestResponse(BaseModel):
    """P1.6: RAG suggestion response."""
    has_suggestion: bool = False
    confidence: float = 0.0
    confidence_level: str = "low"  # "high" | "medium" | "low"
    evidence_refs: List[EvidenceRefResponse] = []
    prompt_chips: List[PromptChipResponse] = []
    suggested_context: str = ""
    datasets_used: List[str] = []
    total_results: int = 0
    trace_id: Optional[str] = None  # P6-6: Observability


@router.post("/suggest", response_model=SuggestResponse)
async def get_rag_suggestion(request: SuggestRequest):
    """
    P1.6: Get RAG-based suggestion with confidence and evidence.
    
    Returns a suggestion card that the user can choose to apply or dismiss.
    Does NOT auto-apply - requires explicit user action.
    
    Example:
        POST /rag/suggest
        {"app_key": "dimension.persona.analyze", "query": "INTJ 성격의 캐릭터 분석"}
        
    Response:
        - has_suggestion: Whether there's a relevant suggestion
        - confidence_level: "high" | "medium" | "low" (user-friendly labels)
        - evidence_refs: Sources with previews
        - prompt_chips: Quick-insert suggestions
    """
    from app.rag.rag_suggestion_service import get_suggestion_service
    
    try:
        service = get_suggestion_service()
        suggestion = service.get_suggestion(
            app_key=request.app_key,
            query=request.query,
            history_context=request.history_context,
            inputs=request.inputs,
        )
        
        # Convert dataclass to Pydantic response
        return SuggestResponse(
            has_suggestion=suggestion.has_suggestion,
            confidence=suggestion.confidence,
            confidence_level=suggestion.confidence_level.value,
            evidence_refs=[
                EvidenceRefResponse(
                    ref_id=e.ref_id,
                    source=e.source,
                    content_preview=e.content_preview,
                    dataset_id=e.dataset_id,
                    dataset_label=e.dataset_label,
                    score=e.score,
                )
                for e in suggestion.evidence_refs
            ],
            prompt_chips=[
                PromptChipResponse(
                    label=c.label,
                    insert_text=c.insert_text,
                    chip_type=c.chip_type,
                )
                for c in suggestion.prompt_chips
            ],
            suggested_context=suggestion.suggested_context,
            datasets_used=suggestion.datasets_used,
            total_results=suggestion.total_results,
            trace_id=suggestion.trace_id,  # P6-6
        )
    except Exception as e:
        logger.error(f"Suggestion request failed: {e}")
        return SuggestResponse(has_suggestion=False)

