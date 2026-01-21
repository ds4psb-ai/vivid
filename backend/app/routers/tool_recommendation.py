"""Tool Recommendation API router for IP-First Coordination Phase 2.5.

Provides endpoints for:
- Tool recommendations based on IP context
- IP-specific tool suggestions
- Tool evidence retrieval

SSoT: IP-First Coordination Roadmap v2.1.1 (Phase 2.5).
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_id
from app.database import get_db
from app.schemas.tool_recommendation import (
    ToolRecommendationRequest,
    ToolRecommendationResponse,
    ToolEvidenceResponse,
    ToolDisplayInfo,
)
from app.services.tool_recommender import (
    ToolRecommenderService,
    create_tool_recommender,
    get_all_tools,
    get_tool_metadata,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tool-recommendation"])


# =============================================================================
# Tool Recommendation Endpoints
# =============================================================================


@router.post("/recommend", response_model=ToolRecommendationResponse)
async def recommend_tools(
    request: ToolRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
) -> ToolRecommendationResponse:
    """Get tool recommendations based on IP/preset context.

    Analyzes the provided context (IP, preset, scene type, user history)
    and returns ranked tool recommendations with confidence scores and
    reason codes explaining why each tool was recommended.

    Args:
        request: Recommendation request with context parameters
        db: Database session
        user_id: Optional authenticated user ID

    Returns:
        ToolRecommendationResponse with ranked recommendations
    """
    logger.info(
        f"[ToolRec] POST /recommend | user={user_id} ip_id={request.ip_id}"
    )

    service = create_tool_recommender(db)

    try:
        response = await service.recommend_tools(request)
        return response
    except Exception as e:
        logger.error(f"[ToolRec] Error in recommend_tools: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.post("/recommend-workflow")
async def recommend_workflow(
    user_prompt: str,
    ip_slug: str,
    content_type: str = "shortform",
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
):
    """Recommend workflow based on user's variation prompt.

    Uses Gemini Flash for intent classification to determine the best
    workflow template for the user's creative intent.

    Args:
        user_prompt: User's variation prompt (e.g., "캐릭터를 INTJ로 변주")
        ip_slug: IP slug for context
        content_type: Content type ("shortform", "anime-mv")

    Returns:
        Dict with workflow_template, steps, and confidence
    """
    logger.info(
        f"[ToolRec] POST /recommend-workflow | user={user_id} prompt={user_prompt[:50]}..."
    )

    service = create_tool_recommender(db)

    try:
        result = await service.recommend_workflow_from_prompt(
            user_prompt=user_prompt,
            ip_slug=ip_slug,
            content_type=content_type,
        )
        return result
    except Exception as e:
        logger.error(f"[ToolRec] Error in recommend_workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to recommend workflow")


@router.get("/ip/{slug}/recommendations", response_model=ToolRecommendationResponse)
async def get_ip_recommendations(
    slug: str,
    max_results: int = Query(default=5, ge=1, le=20),
    scene_type: Optional[str] = Query(default=None),
    dimension_context: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
) -> ToolRecommendationResponse:
    """Get tool recommendations for an IP by slug.

    Convenience endpoint for fetching recommendations when only the IP slug
    is known (e.g., from URL parameters).

    Args:
        slug: IP slug (e.g., "goblin", "squid-game")
        max_results: Maximum number of recommendations (1-20)
        scene_type: Optional scene type hint
        dimension_context: Optional current dimension context
        db: Database session
        user_id: Optional authenticated user ID

    Returns:
        ToolRecommendationResponse with ranked recommendations
    """
    logger.info(
        f"[ToolRec] GET /ip/{slug}/recommendations | user={user_id}"
    )

    service = create_tool_recommender(db)

    try:
        # If no additional context, use simple slug-based recommendations
        if not scene_type and not dimension_context:
            return await service.get_ip_recommendations(slug, max_results)

        # If scene_type or dimension_context provided, build full request
        from sqlalchemy import select
        from app.models_ip import IPCatalog

        result = await db.execute(
            select(IPCatalog).where(IPCatalog.slug == slug)
        )
        ip = result.scalar_one_or_none()

        if not ip:
            return await service.get_ip_recommendations(slug, max_results)

        request = ToolRecommendationRequest(
            ip_id=ip.id,
            scene_type=scene_type,
            dimension_context=dimension_context,
            max_results=max_results,
        )
        return await service.recommend_tools(request)
    except Exception as e:
        logger.error(f"[ToolRec] Error in get_ip_recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/{tool_id}/evidence", response_model=ToolEvidenceResponse)
async def get_tool_evidence(
    tool_id: str,
    ip_id: Optional[UUID] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
) -> ToolEvidenceResponse:
    """Get evidence for a tool selection.

    Returns the evidence references, datasets used, and reason codes
    that support why this tool would be recommended.

    Args:
        tool_id: Tool identifier
        ip_id: Optional IP ID for context-specific evidence
        db: Database session
        user_id: Optional authenticated user ID

    Returns:
        ToolEvidenceResponse with evidence details
    """
    logger.info(
        f"[ToolRec] GET /{tool_id}/evidence | user={user_id} ip_id={ip_id}"
    )

    # Validate tool exists
    metadata = get_tool_metadata(tool_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    service = create_tool_recommender(db)

    try:
        response = await service.get_tool_evidence(tool_id, ip_id)
        return response
    except Exception as e:
        logger.error(f"[ToolRec] Error in get_tool_evidence: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tool evidence")


# =============================================================================
# Tool Metadata Endpoints
# =============================================================================


@router.get("/list", response_model=list[ToolDisplayInfo])
async def list_tools(
    dimension: Optional[str] = Query(default=None, description="Filter by dimension"),
    stage: Optional[str] = Query(default=None, description="Filter by workflow stage"),
) -> list[ToolDisplayInfo]:
    """List all available tools with display info.

    Returns metadata for all tools, optionally filtered by dimension or stage.

    Args:
        dimension: Optional dimension filter (e.g., "AD", "4D", "STORY")
        stage: Optional workflow stage filter (e.g., "planning", "production")

    Returns:
        List of ToolDisplayInfo objects
    """
    logger.info(f"[ToolRec] GET /list | dimension={dimension} stage={stage}")

    all_tools = get_all_tools()
    result: list[ToolDisplayInfo] = []

    for tool in all_tools:
        # Apply filters
        if dimension and tool.get("dimension") != dimension:
            continue
        if stage and tool.get("stage") != stage:
            continue

        result.append(
            ToolDisplayInfo(
                tool_id=tool["tool_id"],
                display_name_ko=tool.get("display_name_ko", tool["tool_id"]),
                display_name_en=tool.get("display_name_en", tool["tool_id"]),
                dimension=tool.get("dimension", ""),
                description_ko="",  # Could be extended to include descriptions
                description_en="",
                icon=f"icon-{tool.get('dimension', 'tool').lower()}",
                base_credits=tool.get("base_credits", 10),
            )
        )

    return result


@router.get("/{tool_id}/info", response_model=ToolDisplayInfo)
async def get_tool_info(
    tool_id: str,
) -> ToolDisplayInfo:
    """Get display info for a specific tool.

    Args:
        tool_id: Tool identifier

    Returns:
        ToolDisplayInfo for the requested tool
    """
    logger.info(f"[ToolRec] GET /{tool_id}/info")

    metadata = get_tool_metadata(tool_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    return ToolDisplayInfo(
        tool_id=metadata["tool_id"],
        display_name_ko=metadata.get("display_name_ko", metadata["tool_id"]),
        display_name_en=metadata.get("display_name_en", metadata["tool_id"]),
        dimension=metadata.get("dimension", ""),
        description_ko="",
        description_en="",
        icon=f"icon-{metadata.get('dimension', 'tool').lower()}",
        base_credits=metadata.get("base_credits", 10),
    )
