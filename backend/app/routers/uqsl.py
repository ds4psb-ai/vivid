"""
UQSL API Router - Universal Quality Selection Layer Endpoints

Endpoints:
- POST /generate: Generate N candidates with quality scores
- POST /select: HITL selection
- POST /feedback: Submit feedback for Thompson Sampling
- POST /three-way: Ensemble++ 3-way comparison
- GET /metrics/{app_key}: Quality metrics for app

2026 Best Practice:
- BackgroundTasks for async history saving
- Pydantic v2 response models
- Proper error handling with HTTPException
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.uqsl.models import (
    CandidateResult,
    QualityScore,
    GenerateCandidatesRequest,
    GenerateCandidatesResponse,
    SelectBestRequest,
    SubmitFeedbackRequest,
    ThreeWayComparisonRequest,
)
from app.uqsl.multi_generate import get_multi_generate_engine
from app.uqsl.quality_evaluator import get_quality_evaluator
from app.uqsl.best_selector import get_best_selector
from app.uqsl.thompson_sampling import get_thompson_sampling_router
from app.uqsl.ensemble_plus_plus import get_ensemble_router

router = APIRouter(prefix="/uqsl", tags=["UQSL"])


# ============================================================================
# Response Models
# ============================================================================

class SelectResponse(BaseModel):
    status: str
    session_id: str


class FeedbackResponse(BaseModel):
    status: str
    updated_arms: list[str]


class ThreeWayResponse(BaseModel):
    results: dict
    recommended: Literal["a", "b", "ab"]
    arms_stats: dict


class QualityMetricsResponse(BaseModel):
    app_key: str
    total_selections: int
    positive_rate: float
    avg_quality_score: float


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/generate", response_model=GenerateCandidatesResponse)
async def generate_candidates(
    request: GenerateCandidatesRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    동일 프롬프트로 N개 후보 생성 후 품질 평가

    - Free tier: 규칙 기반 품질 평가 (LLM 비용 $0)
    - Premium tier: LLM-as-Judge 품질 평가
    """
    try:
        # 1. Get engines
        engine = get_multi_generate_engine()
        evaluator = get_quality_evaluator(tier="free")  # TODO: Get from app config
        selector = get_best_selector()

        # 2. Generate N candidates
        candidates = await engine.generate_candidates(
            prompt=request.prompt,
            app_key=request.app_key,
            n_candidates=request.n_candidates,
        )

        # 3. Get RAG context for quality evaluation (optional)
        context = None
        try:
            from app.rag.hybrid_rag import hybrid_query
            context = await hybrid_query(
                query=request.prompt,
                app_key=request.app_key,
            )
        except Exception:
            pass  # Continue without context

        # 4. Quality evaluation
        scores = await evaluator.evaluate_batch(candidates, context)

        # 5. Best selection
        result = await selector.select_best(
            candidates,
            scores,
            request.strategy,
        )

        # 6. Save history (background)
        background_tasks.add_task(
            _save_selection_history,
            db,
            result.session_id,
            request.app_key,
            request.prompt,
            candidates,
            scores,
            result.selected.idx,
            result.method,
        )

        return GenerateCandidatesResponse(
            session_id=result.session_id,
            candidates=result.all_candidates,
            quality_scores=scores,
            recommended_idx=result.selected.idx,
            method=result.method,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/select", response_model=SelectResponse)
async def select_best(
    request: SelectBestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    사용자가 HITL로 최종 선택

    Updates the selection history with user's choice.
    """
    try:
        # Update selection history with user choice
        # In a full implementation, this would update the database record
        # For now, we just acknowledge the selection

        return SelectResponse(
            status="selected",
            session_id=request.session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selection failed: {str(e)}")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: SubmitFeedbackRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    피드백 제출 + Thompson Sampling 업데이트

    Free tier: 비용 $0 (LLM 호출 없음)
    """
    try:
        # 1. Get Thompson Sampling router
        ts_router = get_thompson_sampling_router()

        # 2. Convert feedback to reward
        reward = request.feedback == "positive"

        # 3. Update arms (in-memory for now)
        # In production, this would also update the database
        updated_arms = []

        # Update default arms based on feedback
        default_arms = ["backend:qdrant_hybrid", "backend:notebooklm"]
        for arm_id in default_arms:
            await ts_router.update(None, arm_id, reward)
            updated_arms.append(arm_id)

        # 4. Sync to BigQuery (background)
        background_tasks.add_task(
            _sync_feedback_to_bigquery,
            request.selection_id,
            request.feedback,
        )

        return FeedbackResponse(
            status="recorded",
            updated_arms=updated_arms,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


@router.post("/three-way", response_model=ThreeWayResponse)
async def three_way_comparison(
    request: ThreeWayComparisonRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ensemble++ 3-Way 비교 (A vs B vs A+B)

    NeurIPS 2025 기반 최신 앙상블 접근법
    """
    try:
        # Get Ensemble++ router
        ensemble_router = get_ensemble_router()

        # Get three-way results
        results = await ensemble_router.get_three_way_results(
            query=request.query,
            dimension=request.dimension,
            auteur_key=request.auteur_key,
        )

        # Get recommended arm
        recommended = await ensemble_router.select_best_arm()

        # Get arm stats
        arm_stats = ensemble_router.get_arm_stats()

        return ThreeWayResponse(
            results={
                "a": results["a"].model_dump(),
                "b": results["b"].model_dump(),
                "ab": results["ab"].model_dump(),
            },
            recommended=recommended,
            arms_stats=arm_stats,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Three-way comparison failed: {str(e)}")


@router.get("/metrics/{app_key}", response_model=QualityMetricsResponse)
async def get_quality_metrics(
    app_key: str,
    db: AsyncSession = Depends(get_db),
):
    """
    앱별 품질 메트릭 조회

    Returns aggregated quality metrics for the app.
    """
    try:
        # In a full implementation, this would query from the database
        # For now, return mock metrics

        return QualityMetricsResponse(
            app_key=app_key,
            total_selections=100,  # Mock
            positive_rate=0.75,    # Mock
            avg_quality_score=0.82, # Mock
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


# ============================================================================
# Background Tasks
# ============================================================================

async def _save_selection_history(
    db: AsyncSession,
    session_id: str,
    app_key: str,
    prompt: str,
    candidates: list[CandidateResult],
    scores: list[QualityScore],
    selected_idx: int,
    method: str,
):
    """Save selection history to database (background task)"""
    try:
        # In production, this would insert into SelectionHistory table
        # For now, just log
        import logging
        logging.info(
            f"UQSL Selection: session={session_id}, app={app_key}, "
            f"candidates={len(candidates)}, selected={selected_idx}, method={method}"
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to save selection history: {e}")


async def _sync_feedback_to_bigquery(
    selection_id: str,
    feedback: str,
):
    """Sync feedback to BigQuery (background task)"""
    try:
        # In production, this would stream to BigQuery
        # For now, just log
        import logging
        logging.info(f"UQSL Feedback: selection={selection_id}, feedback={feedback}")
    except Exception as e:
        import logging
        logging.error(f"Failed to sync feedback to BigQuery: {e}")
