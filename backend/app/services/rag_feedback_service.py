"""P6: RAG Feedback Service.

Provides functions to:
- Store RAG responses for feedback linking
- Collect explicit/implicit feedback
- Query feedback metrics

Usage:
    from app.services.rag_feedback_service import (
        store_rag_response,
        submit_explicit_feedback,
        track_implicit_feedback,
        get_feedback_metrics,
    )
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_feedback import RAGResponse, RAGFeedback, RAGResponseDailyStats
from app.schemas.rag_feedback_schemas import (
    ExplicitFeedbackCreate,
    ImplicitFeedbackCreate,
    RAGResponseCreate,
    FeedbackMetrics,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Type Import for HybridRAGResult (avoid circular import)
# =============================================================================

# Lazy import to avoid circular dependency
def _get_hybrid_rag_result_type():
    from app.rag.hybrid_rag import HybridRAGResult
    return HybridRAGResult


# =============================================================================
# Helper Functions
# =============================================================================


def compute_query_hash(query: str) -> str:
    """Compute SHA256 hash for query grouping."""
    normalized = query.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


# =============================================================================
# RAG Response Storage
# =============================================================================


async def store_rag_response(
    db: AsyncSession,
    data: RAGResponseCreate,
) -> RAGResponse:
    """Store RAG response for feedback linking.

    Called automatically by hybrid_query() after generating a response.

    Args:
        db: Database session
        data: RAG response data

    Returns:
        Created RAGResponse record
    """
    try:
        response = RAGResponse(
            id=uuid4(),
            query=data.query,
            query_hash=data.query_hash or compute_query_hash(data.query),
            answer=data.answer,
            # P5 Classification
            query_type=data.query_type,
            classification_confidence=data.classification_confidence,
            classifier_used=data.classifier_used,
            # Strategy
            strategy_used=data.strategy_used,
            retrieval_skipped=data.retrieval_skipped,
            # Metrics
            latency_ms=data.latency_ms,
            retrieval_count=data.retrieval_count,
            reranked=data.reranked,
            rerank_latency_ms=data.rerank_latency_ms,
            crag_triggered=data.crag_triggered,
            grounded=data.grounded,
            # Sources
            sources=data.sources,
            source_scores=data.source_scores,
            # RRF
            rrf_enabled=data.rrf_enabled,
            keyword_results_count=data.keyword_results_count,
            vector_results_count=data.vector_results_count,
            # Context
            app_key=data.app_key,
            dimension=data.dimension,
            auteur_key=data.auteur_key,
            user_id=data.user_id,
            session_id=data.session_id,
            # Error
            error=data.error,
            error_type=data.error_type,
        )

        db.add(response)
        await db.commit()
        await db.refresh(response)

        logger.debug(f"[RAGFeedback] Stored response {response.id} for query '{data.query[:30]}...'")
        return response

    except Exception as e:
        logger.error(f"[RAGFeedback] Failed to store response: {e}")
        await db.rollback()
        raise


async def store_hybrid_result(
    db: AsyncSession,
    query: str,
    result: Any,  # HybridRAGResult - use Any to avoid circular import
    app_key: Optional[str] = None,
    user_id: Optional[UUID] = None,
    session_id: Optional[str] = None,
) -> RAGResponse:
    """Store HybridRAGResult for feedback tracking.

    Convenience wrapper that extracts fields from HybridRAGResult
    and stores them in the database.

    Args:
        db: Database session
        query: Original query string
        result: HybridRAGResult from hybrid_query()
        app_key: Application key
        user_id: User ID
        session_id: Session ID

    Returns:
        Created RAGResponse with ID for feedback linking
    """
    # Build sources list from result
    sources = []
    for src in result.notebooklm_sources:
        sources.append({
            "source_id": getattr(src, "source_id", None),
            "type": "notebooklm",
            "title": getattr(src, "title", None),
        })
    for src in result.vertex_sources:
        sources.append({
            "source_id": getattr(src, "source_id", None),
            "type": "vertex",
            "title": getattr(src, "title", None),
            "score": getattr(src, "score", None),
        })

    data = RAGResponseCreate(
        query=query,
        query_hash=compute_query_hash(query),
        answer=result.answer,
        # P5 Classification
        query_type=getattr(result, "query_type", None),
        classification_confidence=getattr(result, "classification_confidence", None),
        classifier_used=None,  # Set by classifier layer if needed
        # Strategy
        strategy_used=result.strategy_used,
        retrieval_skipped=getattr(result, "retrieval_skipped", False),
        # Metrics
        latency_ms=result.query_time_ms,
        retrieval_count=result.retrieval_count,
        reranked=result.reranked,
        crag_triggered=getattr(result, "crag_triggered", False),
        grounded=result.grounded,
        # Sources
        sources=sources if sources else None,
        source_scores=result.source_scores if result.source_scores else None,
        # RRF
        rrf_enabled=result.rrf_enabled,
        keyword_results_count=result.keyword_results_count,
        vector_results_count=result.vector_results_count,
        # Context
        app_key=app_key,
        dimension=result.dimension,
        auteur_key=result.auteur_key,
        user_id=user_id,
        session_id=session_id,
    )

    response = await store_rag_response(db, data)

    # Attach response_id to result for client use
    result.response_id = str(response.id)

    return response


async def get_rag_response(
    db: AsyncSession,
    response_id: UUID,
) -> Optional[RAGResponse]:
    """Get RAG response by ID."""
    result = await db.execute(
        select(RAGResponse).where(RAGResponse.id == response_id)
    )
    return result.scalar_one_or_none()


# =============================================================================
# Explicit Feedback
# =============================================================================


async def submit_explicit_feedback(
    db: AsyncSession,
    data: ExplicitFeedbackCreate,
    user_id: Optional[UUID] = None,
    user_agent: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> RAGFeedback:
    """Submit explicit feedback (rating, thumbs_up/down, report).

    Args:
        db: Database session
        data: Explicit feedback data
        user_id: User ID (optional)
        user_agent: User agent string
        client_ip: Client IP address

    Returns:
        Created RAGFeedback record

    Raises:
        ValueError: If response_id doesn't exist
    """
    # Verify response exists
    response = await get_rag_response(db, data.response_id)
    if not response:
        raise ValueError(f"RAG response {data.response_id} not found")

    try:
        feedback = RAGFeedback(
            id=uuid4(),
            response_id=data.response_id,
            # Explicit feedback
            rating=data.rating,
            feedback_type=data.feedback_type.value if data.feedback_type else None,
            user_comment=data.comment,
            # Metadata
            user_id=user_id,
            user_agent=user_agent[:500] if user_agent else None,
            client_ip=client_ip,
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        logger.info(
            f"[RAGFeedback] Explicit feedback {feedback.id} submitted for response {data.response_id} "
            f"(rating={data.rating}, type={data.feedback_type})"
        )
        return feedback

    except Exception as e:
        logger.error(f"[RAGFeedback] Failed to submit explicit feedback: {e}")
        await db.rollback()
        raise


# =============================================================================
# Implicit Feedback
# =============================================================================


async def track_implicit_feedback(
    db: AsyncSession,
    data: ImplicitFeedbackCreate,
    user_id: Optional[UUID] = None,
    user_agent: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> RAGFeedback:
    """Track implicit feedback (clicks, copies, reformulations).

    Args:
        db: Database session
        data: Implicit feedback data
        user_id: User ID (optional)
        user_agent: User agent string
        client_ip: Client IP address

    Returns:
        Created RAGFeedback record

    Raises:
        ValueError: If response_id doesn't exist
    """
    # Verify response exists
    response = await get_rag_response(db, data.response_id)
    if not response:
        raise ValueError(f"RAG response {data.response_id} not found")

    try:
        feedback = RAGFeedback(
            id=uuid4(),
            response_id=data.response_id,
            implicit_event_type=data.event_type.value,
            # Source click
            source_clicked=(data.event_type.value == "source_click"),
            clicked_source_id=data.source_id,
            clicked_source_index=data.source_index,
            # Session
            session_duration_ms=data.duration_ms,
            # Reformulation
            query_reformulated=(data.event_type.value == "query_reformulate"),
            reformulated_query=data.new_query,
            time_to_reformulate_ms=data.duration_ms if data.event_type.value == "query_reformulate" else None,
            # Copy
            text_copied=(data.event_type.value == "text_copy"),
            copied_length=data.copied_length,
            # Metadata
            user_id=user_id,
            user_agent=user_agent[:500] if user_agent else None,
            client_ip=client_ip,
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        logger.debug(
            f"[RAGFeedback] Implicit feedback {feedback.id} tracked for response {data.response_id} "
            f"(event={data.event_type})"
        )
        return feedback

    except Exception as e:
        logger.error(f"[RAGFeedback] Failed to track implicit feedback: {e}")
        await db.rollback()
        raise


# =============================================================================
# Feedback Queries
# =============================================================================


async def get_feedbacks_for_response(
    db: AsyncSession,
    response_id: UUID,
) -> List[RAGFeedback]:
    """Get all feedbacks for a response."""
    result = await db.execute(
        select(RAGFeedback)
        .where(RAGFeedback.response_id == response_id)
        .order_by(RAGFeedback.created_at.desc())
    )
    return list(result.scalars().all())


async def get_recent_responses(
    db: AsyncSession,
    app_key: Optional[str] = None,
    days: int = 7,
    limit: int = 100,
) -> List[RAGResponse]:
    """Get recent RAG responses."""
    since = datetime.utcnow() - timedelta(days=days)

    query = select(RAGResponse).where(RAGResponse.created_at >= since)

    if app_key:
        query = query.where(RAGResponse.app_key == app_key)

    query = query.order_by(RAGResponse.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


# =============================================================================
# Feedback Metrics
# =============================================================================


async def get_feedback_metrics(
    db: AsyncSession,
    app_key: Optional[str] = None,
    days: int = 7,
) -> FeedbackMetrics:
    """Get feedback metrics for an app.

    Args:
        db: Database session
        app_key: Filter by app key (None for all)
        days: Number of days to analyze

    Returns:
        FeedbackMetrics with aggregated data
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Base query filter
    response_filter = RAGResponse.created_at >= since
    if app_key:
        response_filter = and_(response_filter, RAGResponse.app_key == app_key)

    # Total queries
    total_result = await db.execute(
        select(func.count(RAGResponse.id)).where(response_filter)
    )
    total_queries = total_result.scalar() or 0

    # Skip retrieval count
    skip_result = await db.execute(
        select(func.count(RAGResponse.id))
        .where(and_(response_filter, RAGResponse.retrieval_skipped == True))  # noqa
    )
    skip_retrieval_count = skip_result.scalar() or 0

    # Average latency and retrieval count
    avg_result = await db.execute(
        select(
            func.avg(RAGResponse.latency_ms),
            func.avg(RAGResponse.retrieval_count),
        ).where(response_filter)
    )
    avg_row = avg_result.one()
    avg_latency_ms = float(avg_row[0] or 0)
    avg_retrieval_count = float(avg_row[1] or 0)

    # Feedback counts - join with feedbacks
    feedback_result = await db.execute(
        select(
            func.count(RAGFeedback.id),
            func.avg(RAGFeedback.rating),
        )
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(response_filter)
    )
    feedback_row = feedback_result.one()
    feedback_count = feedback_row[0] or 0
    avg_rating = float(feedback_row[1]) if feedback_row[1] else None

    # Thumbs up/down/report counts
    thumbs_result = await db.execute(
        select(
            func.count(RAGFeedback.id).filter(RAGFeedback.feedback_type == "thumbs_up"),
            func.count(RAGFeedback.id).filter(RAGFeedback.feedback_type == "thumbs_down"),
            func.count(RAGFeedback.id).filter(RAGFeedback.feedback_type == "report"),
        )
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(response_filter)
    )
    thumbs_row = thumbs_result.one()
    thumbs_up_count = thumbs_row[0] or 0
    thumbs_down_count = thumbs_row[1] or 0
    report_count = thumbs_row[2] or 0

    # Implicit feedback rates
    implicit_result = await db.execute(
        select(
            func.count(RAGFeedback.id).filter(RAGFeedback.source_clicked == True),  # noqa
            func.count(RAGFeedback.id).filter(RAGFeedback.query_reformulated == True),  # noqa
            func.count(RAGFeedback.id).filter(RAGFeedback.text_copied == True),  # noqa
        )
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(response_filter)
    )
    implicit_row = implicit_result.one()
    source_clicks = implicit_row[0] or 0
    reformulations = implicit_row[1] or 0
    copies = implicit_row[2] or 0

    # Query type distribution
    type_result = await db.execute(
        select(RAGResponse.query_type, func.count(RAGResponse.id))
        .where(response_filter)
        .group_by(RAGResponse.query_type)
    )
    query_type_distribution = {
        row[0] or "unknown": row[1] for row in type_result.all()
    }

    # Strategy distribution
    strategy_result = await db.execute(
        select(RAGResponse.strategy_used, func.count(RAGResponse.id))
        .where(response_filter)
        .group_by(RAGResponse.strategy_used)
    )
    strategy_distribution = {
        row[0] or "unknown": row[1] for row in strategy_result.all()
    }

    return FeedbackMetrics(
        app_key=app_key,
        period_days=days,
        total_queries=total_queries,
        skip_retrieval_count=skip_retrieval_count,
        skip_retrieval_rate=skip_retrieval_count / total_queries if total_queries > 0 else 0,
        avg_latency_ms=avg_latency_ms,
        avg_retrieval_count=avg_retrieval_count,
        feedback_count=feedback_count,
        feedback_rate=feedback_count / total_queries if total_queries > 0 else 0,
        avg_rating=avg_rating,
        thumbs_up_count=thumbs_up_count,
        thumbs_down_count=thumbs_down_count,
        report_count=report_count,
        source_click_rate=source_clicks / total_queries if total_queries > 0 else 0,
        reformulation_rate=reformulations / total_queries if total_queries > 0 else 0,
        copy_rate=copies / total_queries if total_queries > 0 else 0,
        query_type_distribution=query_type_distribution,
        strategy_distribution=strategy_distribution,
    )


# =============================================================================
# Daily Stats Aggregation
# =============================================================================


async def aggregate_daily_stats(
    db: AsyncSession,
    stat_date: datetime,
    app_key: Optional[str] = None,
) -> RAGResponseDailyStats:
    """Aggregate daily stats for P7 analysis.

    Should be called daily by a cron job.

    Args:
        db: Database session
        stat_date: Date to aggregate
        app_key: Filter by app key (None for global stats)

    Returns:
        Created or updated RAGResponseDailyStats
    """
    start = stat_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    # Base filter
    response_filter = and_(
        RAGResponse.created_at >= start,
        RAGResponse.created_at < end,
    )
    if app_key:
        response_filter = and_(response_filter, RAGResponse.app_key == app_key)

    # Aggregate metrics
    metrics_result = await db.execute(
        select(
            func.count(RAGResponse.id),
            func.count(RAGResponse.id).filter(RAGResponse.retrieval_skipped == True),  # noqa
            func.count(RAGResponse.id).filter(RAGResponse.crag_triggered == True),  # noqa
            func.count(RAGResponse.id).filter(RAGResponse.error.isnot(None)),
            func.avg(RAGResponse.latency_ms),
            func.avg(RAGResponse.retrieval_count),
            func.avg(RAGResponse.classification_confidence),
        ).where(response_filter)
    )
    metrics_row = metrics_result.one()

    # Feedback aggregates
    feedback_result = await db.execute(
        select(
            func.count(RAGFeedback.id),
            func.avg(RAGFeedback.rating),
            func.count(RAGFeedback.id).filter(RAGFeedback.feedback_type == "thumbs_up"),
            func.count(RAGFeedback.id).filter(RAGFeedback.feedback_type == "thumbs_down"),
            func.count(RAGFeedback.id).filter(RAGFeedback.source_clicked == True),  # noqa
            func.count(RAGFeedback.id).filter(RAGFeedback.query_reformulated == True),  # noqa
            func.count(RAGFeedback.id).filter(RAGFeedback.text_copied == True),  # noqa
        )
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(response_filter)
    )
    feedback_row = feedback_result.one()

    total_queries = metrics_row[0] or 0

    stats = RAGResponseDailyStats(
        id=uuid4(),
        stat_date=start,
        app_key=app_key,
        total_queries=total_queries,
        skip_retrieval_count=metrics_row[1] or 0,
        crag_trigger_count=metrics_row[2] or 0,
        error_count=metrics_row[3] or 0,
        avg_latency_ms=float(metrics_row[4]) if metrics_row[4] else None,
        avg_retrieval_count=float(metrics_row[5]) if metrics_row[5] else None,
        avg_confidence=float(metrics_row[6]) if metrics_row[6] else None,
        feedback_count=feedback_row[0] or 0,
        avg_rating=float(feedback_row[1]) if feedback_row[1] else None,
        thumbs_up_count=feedback_row[2] or 0,
        thumbs_down_count=feedback_row[3] or 0,
        source_click_rate=(feedback_row[4] or 0) / total_queries if total_queries > 0 else None,
        reformulation_rate=(feedback_row[5] or 0) / total_queries if total_queries > 0 else None,
        copy_rate=(feedback_row[6] or 0) / total_queries if total_queries > 0 else None,
    )

    db.add(stats)
    await db.commit()
    await db.refresh(stats)

    logger.info(f"[RAGFeedback] Aggregated daily stats for {start.date()} (app={app_key}, queries={total_queries})")
    return stats


# =============================================================================
# Response with Feedback
# =============================================================================


async def get_response_with_feedback(
    db: AsyncSession,
    response_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Get RAG response with feedback summary.

    Args:
        db: Database session
        response_id: Response UUID

    Returns:
        Response dict with feedback_count and avg_rating
    """
    response = await get_rag_response(db, response_id)
    if not response:
        return None

    # Get feedback summary
    feedback_result = await db.execute(
        select(
            func.count(RAGFeedback.id),
            func.avg(RAGFeedback.rating),
        )
        .where(RAGFeedback.response_id == response_id)
    )
    feedback_row = feedback_result.one()

    return {
        "id": response.id,
        "query": response.query,
        "query_hash": response.query_hash,
        "answer": response.answer,
        "query_type": response.query_type,
        "classification_confidence": response.classification_confidence,
        "strategy_used": response.strategy_used,
        "retrieval_skipped": response.retrieval_skipped,
        "latency_ms": response.latency_ms,
        "retrieval_count": response.retrieval_count,
        "reranked": response.reranked,
        "crag_triggered": response.crag_triggered,
        "grounded": response.grounded,
        "app_key": response.app_key,
        "dimension": response.dimension,
        "auteur_key": response.auteur_key,
        "created_at": response.created_at,
        "feedback_count": feedback_row[0] or 0,
        "avg_rating": float(feedback_row[1]) if feedback_row[1] else None,
    }


# =============================================================================
# Daily Stats Query
# =============================================================================


async def get_daily_stats(
    db: AsyncSession,
    app_key: Optional[str] = None,
    days: int = 7,
) -> List[RAGResponseDailyStats]:
    """Get daily stats for trend analysis.

    Args:
        db: Database session
        app_key: Filter by app key
        days: Number of days

    Returns:
        List of daily stats
    """
    since = datetime.utcnow() - timedelta(days=days)

    query = select(RAGResponseDailyStats).where(
        RAGResponseDailyStats.stat_date >= since
    )

    if app_key:
        query = query.where(RAGResponseDailyStats.app_key == app_key)

    query = query.order_by(RAGResponseDailyStats.stat_date.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


# =============================================================================
# Classification Accuracy (P7 Preparation)
# =============================================================================


async def get_classification_accuracy_metrics(
    db: AsyncSession,
    days: int = 7,
) -> Dict[str, Any]:
    """Get P5 classification accuracy metrics.

    Analyzes correlation between classification and user feedback
    for P7 self-correction threshold tuning.

    Args:
        db: Database session
        days: Analysis period

    Returns:
        Classification accuracy metrics dict
    """
    from app.schemas.rag_feedback_schemas import ClassificationAccuracyMetrics

    since = datetime.utcnow() - timedelta(days=days)

    # Total classified queries
    total_result = await db.execute(
        select(func.count(RAGResponse.id))
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.query_type.isnot(None),
        ))
    )
    total_classified = total_result.scalar() or 0

    # Queries with feedback
    with_feedback_result = await db.execute(
        select(func.count(func.distinct(RAGFeedback.response_id)))
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.query_type.isnot(None),
        ))
    )
    with_feedback = with_feedback_result.scalar() or 0

    # Positive feedback rate (rating >= 4 or thumbs_up)
    positive_result = await db.execute(
        select(func.count(RAGFeedback.id))
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.query_type.isnot(None),
            or_(
                RAGFeedback.rating >= 4,
                RAGFeedback.feedback_type == "thumbs_up",
            ),
        ))
    )
    positive_count = positive_result.scalar() or 0

    total_feedback_result = await db.execute(
        select(func.count(RAGFeedback.id))
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.query_type.isnot(None),
        ))
    )
    total_feedback = total_feedback_result.scalar() or 0

    positive_feedback_rate = positive_count / total_feedback if total_feedback > 0 else 0

    # Per query type accuracy
    type_accuracy_result = await db.execute(
        select(
            RAGResponse.query_type,
            func.count(RAGFeedback.id).filter(
                or_(RAGFeedback.rating >= 4, RAGFeedback.feedback_type == "thumbs_up")
            ),
            func.count(RAGFeedback.id),
        )
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.query_type.isnot(None),
        ))
        .group_by(RAGResponse.query_type)
    )

    accuracy_by_type = {}
    for row in type_accuracy_result.all():
        query_type = row[0] or "unknown"
        positive = row[1] or 0
        total = row[2] or 0
        accuracy_by_type[query_type] = {
            "positive_rate": positive / total if total > 0 else 0,
            "total_feedback": total,
        }

    # Skip retrieval analysis
    skip_total_result = await db.execute(
        select(func.count(RAGResponse.id))
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.retrieval_skipped == True,  # noqa
        ))
    )
    skip_retrieval_total = skip_total_result.scalar() or 0

    skip_positive_result = await db.execute(
        select(func.count(RAGFeedback.id))
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.retrieval_skipped == True,  # noqa
            or_(RAGFeedback.rating >= 4, RAGFeedback.feedback_type == "thumbs_up"),
        ))
    )
    skip_positive = skip_positive_result.scalar() or 0

    skip_negative_result = await db.execute(
        select(func.count(RAGFeedback.id))
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.retrieval_skipped == True,  # noqa
            or_(RAGFeedback.rating <= 2, RAGFeedback.feedback_type == "thumbs_down"),
        ))
    )
    skip_negative_cases = skip_negative_result.scalar() or 0

    skip_feedback_total = await db.execute(
        select(func.count(RAGFeedback.id))
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.retrieval_skipped == True,  # noqa
        ))
    )
    skip_feedback = skip_feedback_total.scalar() or 0
    skip_positive_rate = skip_positive / skip_feedback if skip_feedback > 0 else 0

    # CRAG trigger analysis
    crag_total_result = await db.execute(
        select(func.count(RAGResponse.id))
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.crag_triggered == True,  # noqa
        ))
    )
    crag_total = crag_total_result.scalar() or 0
    crag_trigger_rate = crag_total / total_classified if total_classified > 0 else 0

    crag_positive_result = await db.execute(
        select(func.count(RAGFeedback.id))
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.crag_triggered == True,  # noqa
            or_(RAGFeedback.rating >= 4, RAGFeedback.feedback_type == "thumbs_up"),
        ))
    )
    crag_positive = crag_positive_result.scalar() or 0

    crag_feedback_total = await db.execute(
        select(func.count(RAGFeedback.id))
        .select_from(RAGFeedback)
        .join(RAGResponse)
        .where(and_(
            RAGResponse.created_at >= since,
            RAGResponse.crag_triggered == True,  # noqa
        ))
    )
    crag_feedback = crag_feedback_total.scalar() or 0
    crag_success_rate = crag_positive / crag_feedback if crag_feedback > 0 else 0

    # Recommendations (placeholder - P7 will implement logic)
    recommended_threshold_adjustments = {}
    if skip_positive_rate < 0.7:
        recommended_threshold_adjustments["skip_confidence_threshold"] = 0.05  # Increase
    if crag_success_rate < 0.6:
        recommended_threshold_adjustments["crag_trigger_threshold"] = -0.05  # Lower

    return ClassificationAccuracyMetrics(
        period_days=days,
        total_classified=total_classified,
        with_feedback=with_feedback,
        positive_feedback_rate=positive_feedback_rate,
        accuracy_by_type=accuracy_by_type,
        skip_retrieval_total=skip_retrieval_total,
        skip_positive_rate=skip_positive_rate,
        skip_negative_cases=skip_negative_cases,
        crag_trigger_rate=crag_trigger_rate,
        crag_success_rate=crag_success_rate,
        recommended_threshold_adjustments=recommended_threshold_adjustments,
    )
