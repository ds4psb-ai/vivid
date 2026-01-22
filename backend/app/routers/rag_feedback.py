"""P6: RAG Feedback API Router.

Endpoints for collecting explicit and implicit feedback on RAG responses.
Supports P5 classification accuracy analysis and P7 self-correction.

Endpoints:
    POST /rag/feedback/explicit - Submit explicit feedback (rating, thumbs)
    POST /rag/feedback/implicit - Track implicit feedback (clicks, copies)
    GET /rag/feedback/metrics - Get aggregated feedback metrics
    GET /rag/feedback/response/{response_id} - Get response with feedback
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_optional
from app.utils.error_sanitize import safe_error_detail
from app.schemas.rag_feedback_schemas import (
    ExplicitFeedbackCreate,
    ImplicitFeedbackCreate,
    FeedbackSubmitResponse,
    RAGResponseRead,
    RAGFeedbackRead,
    FeedbackMetrics,
    ClassificationAccuracyMetrics,
    DailyStatsRead,
)
from app.services import rag_feedback_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag/feedback", tags=["rag-feedback"])


# =============================================================================
# Helper Functions
# =============================================================================


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# =============================================================================
# Feedback Submission Endpoints
# =============================================================================


@router.post("/explicit", response_model=FeedbackSubmitResponse, status_code=201)
async def submit_explicit_feedback(
    data: ExplicitFeedbackCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """Submit explicit feedback for a RAG response.

    Explicit feedback includes:
    - rating: 1-5 star rating
    - feedback_type: thumbs_up, thumbs_down, or report
    - comment: Optional text comment

    At least one of rating, feedback_type, or comment must be provided.
    """
    # Validate at least one field is provided
    if data.rating is None and data.feedback_type is None and data.comment is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of rating, feedback_type, or comment must be provided"
        )

    user_id = UUID(current_user["id"]) if current_user else None
    user_agent = request.headers.get("User-Agent")
    client_ip = get_client_ip(request)

    try:
        feedback = await rag_feedback_service.submit_explicit_feedback(
            db=db,
            data=data,
            user_id=user_id,
            user_agent=user_agent,
            client_ip=client_ip,
        )

        return FeedbackSubmitResponse(
            feedback_id=feedback.id,
            response_id=feedback.response_id,
            message="Explicit feedback submitted successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_error_detail(e, "RAG feedback lookup"))
    except Exception as e:
        logger.error(f"Failed to submit explicit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.post("/implicit", response_model=FeedbackSubmitResponse, status_code=201)
async def track_implicit_feedback(
    data: ImplicitFeedbackCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """Track implicit feedback for a RAG response.

    Implicit feedback tracks user behavior:
    - source_click: User clicked on a source reference
    - text_copy: User copied text from the response
    - query_reformulate: User rephrased their query
    - session_end: User session ended

    These signals help analyze response quality indirectly.
    """
    user_id = UUID(current_user["id"]) if current_user else None
    user_agent = request.headers.get("User-Agent")
    client_ip = get_client_ip(request)

    try:
        feedback = await rag_feedback_service.track_implicit_feedback(
            db=db,
            data=data,
            user_id=user_id,
            user_agent=user_agent,
            client_ip=client_ip,
        )

        return FeedbackSubmitResponse(
            feedback_id=feedback.id,
            response_id=feedback.response_id,
            message=f"Implicit feedback ({data.event_type.value}) tracked successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_error_detail(e, "RAG feedback lookup"))
    except Exception as e:
        logger.error(f"Failed to track implicit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to track feedback")


# =============================================================================
# Analytics Endpoints
# =============================================================================


@router.get("/metrics", response_model=FeedbackMetrics)
async def get_feedback_metrics(
    app_key: Optional[str] = Query(None, description="Filter by app_key"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated feedback metrics.

    Returns comprehensive metrics including:
    - Query counts and skip rates
    - Performance averages (latency, retrieval count)
    - Explicit feedback breakdown (thumbs up/down, ratings)
    - Implicit signal rates (clicks, copies, reformulations)
    - P5 classification distribution

    Useful for monitoring RAG quality and identifying issues.
    """
    try:
        metrics = await rag_feedback_service.get_feedback_metrics(
            db=db,
            app_key=app_key,
            days=days,
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to get feedback metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/classification-accuracy", response_model=ClassificationAccuracyMetrics)
async def get_classification_accuracy(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get P5 classification accuracy metrics.

    Analyzes how well the query classifier is performing by correlating
    classification decisions with user feedback. Used for P7 self-correction.

    Returns:
    - Overall accuracy based on positive/negative feedback
    - Per-query-type accuracy breakdown
    - Skip retrieval success rate
    - CRAG trigger effectiveness
    - Recommended threshold adjustments
    """
    try:
        metrics = await rag_feedback_service.get_classification_accuracy_metrics(
            db=db,
            days=days,
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to get classification accuracy: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve accuracy metrics")


@router.get("/daily-stats", response_model=list[DailyStatsRead])
async def get_daily_stats(
    app_key: Optional[str] = Query(None, description="Filter by app_key"),
    days: int = Query(7, ge=1, le=30, description="Number of days"),
    db: AsyncSession = Depends(get_db),
):
    """Get daily aggregated statistics.

    Returns pre-computed daily stats useful for trend analysis
    and P7 self-correction monitoring.
    """
    try:
        stats = await rag_feedback_service.get_daily_stats(
            db=db,
            app_key=app_key,
            days=days,
        )
        return stats
    except Exception as e:
        logger.error(f"Failed to get daily stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve daily stats")


# =============================================================================
# Response Lookup Endpoints
# =============================================================================


@router.get("/response/{response_id}", response_model=RAGResponseRead)
async def get_response(
    response_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a RAG response by ID with feedback summary.

    Returns the stored RAG response along with aggregated feedback
    information (count and average rating).
    """
    try:
        response = await rag_feedback_service.get_response_with_feedback(
            db=db,
            response_id=response_id,
        )
        if not response:
            raise HTTPException(status_code=404, detail="Response not found")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get response: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve response")


@router.get("/response/{response_id}/feedbacks", response_model=list[RAGFeedbackRead])
async def get_response_feedbacks(
    response_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all feedbacks for a specific RAG response.

    Returns a list of all explicit and implicit feedback entries
    associated with the given response.
    """
    try:
        feedbacks = await rag_feedback_service.get_feedbacks_for_response(
            db=db,
            response_id=response_id,
        )
        return feedbacks
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_error_detail(e, "RAG feedback lookup"))
    except Exception as e:
        logger.error(f"Failed to get feedbacks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedbacks")
