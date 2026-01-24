"""
UQSL Router - Universal Quality Selection Layer API

Endpoints:
- POST /generate: Generate N candidates and select best
- POST /select: HITL selection (human-in-the-loop)
- POST /feedback: Submit user feedback for Thompson Sampling
- POST /three-way: Ensemble++ 3-way comparison
- GET /metrics/{app_key}: Quality metrics for app
- GET /arms: Get Thompson Sampling arm statistics
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from typing import Optional, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.middleware.rate_limit import limiter, RATE_LIMIT_UQSL_MULTI
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.sse_utils import (
    sse_progress,
    sse_complete,
    sse_error,
    sse_heartbeat,
    sse_event,
    get_sse_headers,
)

logger = logging.getLogger(__name__)
from app.models_uqsl import SelectionHistory, EnsembleComparison, BanditArm, UQSLConfig
from app.uqsl.models import (
    GenerateCandidatesRequest,
    GenerateCandidatesResponse,
    SelectBestRequest,
    SubmitFeedbackRequest,
    ThreeWayComparisonRequest,
    ThreeWayResult,
    QualityScore,
    CandidateResult,
)
from app.uqsl.multi_generate import get_multi_generate_engine
from app.uqsl.quality_evaluator import get_quality_evaluator
from app.uqsl.best_selector import get_best_selector
from app.uqsl.thompson_sampling import get_thompson_sampling_router, get_initialized_router
from app.uqsl.session_cache import get_session_cache, UQSLSessionCache

router = APIRouter(prefix="/api/v1/uqsl", tags=["uqsl"])

# Redis-backed session cache (2026 Best Practice)
# Fallback to in-memory if Redis unavailable
# Lazy initialization to allow mocking in tests
_session_cache: UQSLSessionCache | None = None


def _get_session_cache() -> UQSLSessionCache:
    """Get session cache with lazy initialization."""
    global _session_cache
    if _session_cache is None:
        _session_cache = get_session_cache()
    return _session_cache


# Legacy compatibility alias (for imports from other modules)
# Use _get_session_cache().get/set instead of direct dict access
_sessions: dict[str, dict] = {}  # Deprecated: Use _get_session_cache()


@router.post("/generate", response_model=GenerateCandidatesResponse)
@limiter.limit(RATE_LIMIT_UQSL_MULTI)
async def generate_candidates(
    request: Request,
    body: GenerateCandidatesRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate N candidates and optionally auto-select best.

    Flow:
    1. MultiGenerateEngine generates N candidates in parallel
    2. QualityEvaluator scores each candidate
    3. BestSelector chooses best based on strategy
    4. Results stored in session for HITL if needed
    """
    engine = get_multi_generate_engine()
    evaluator = get_quality_evaluator()
    selector = get_best_selector()

    # Initialize Thompson Sampling router
    ts_router = await get_initialized_router(db)

    # 1. Generate candidates
    candidates = await engine.generate_candidates(
        prompt=body.prompt,
        app_key=body.app_key,
        n_candidates=body.n_candidates,
    )

    # 2. Evaluate quality
    scores = await evaluator.evaluate_batch(candidates)

    # 3. Select best
    result = await selector.select_best(
        candidates=candidates,
        scores=scores,
        strategy=body.strategy,
    )

    # 4. Store session for potential HITL (Redis-backed, 2026 Best Practice)
    prompt_hash = hashlib.sha256(body.prompt.encode()).hexdigest()[:64]
    await _get_session_cache().set(result.session_id, {
        "candidates": [c.model_dump() for c in candidates],
        "scores": [s.model_dump() for s in scores],
        "prompt_hash": prompt_hash,
        "prompt_preview": body.prompt[:200],
        "app_key": body.app_key,
        "strategy": body.strategy,
        "arms_used": result.arms_used,
        "created_at": datetime.utcnow().isoformat(),
    })

    # 5. Record selection history
    try:
        history = SelectionHistory(
            app_key=body.app_key,
            prompt_hash=prompt_hash,
            prompt_preview=body.prompt[:200],
            n_candidates=len(candidates),
            candidates_data={"candidates": [c.model_dump() for c in candidates]},
            quality_scores={"scores": [s.model_dump() for s in scores]},
            selected_idx=result.selected.idx,
            selection_method=result.method,
            selection_confidence=result.confidence,
            arms_used=result.arms_used,
            dimension=body.app_key.split(".")[-1] if "." in body.app_key else None,
        )
        db.add(history)
        await db.commit()
    except Exception:
        # Don't fail request if history recording fails
        pass

    return GenerateCandidatesResponse(
        session_id=result.session_id,
        candidates=result.all_candidates,
        quality_scores=scores,
        recommended_idx=result.selected.idx,
        method=result.method,
    )


@router.post("/generate/stream")
async def generate_candidates_stream(
    request: GenerateCandidatesRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    SSE streaming endpoint for N-candidate generation with real-time updates.

    2026 Best Practice:
    - Real-time progress for each candidate generation
    - Quality score streaming as evaluated
    - Thompson Sampling arm selection events

    Events:
    - progress: Generation progress (percent, message, stage)
    - candidate: Individual candidate result
    - quality: Quality score for candidate
    - selection: Final selection with recommendation
    - complete: Final response
    - error: Error event
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        start_time = time.perf_counter()
        session_id = str(uuid.uuid4())

        try:
            yield sse_progress(1, "UQSL 생성 시작...", "starting")

            engine = get_multi_generate_engine()
            evaluator = get_quality_evaluator()
            selector = get_best_selector()
            ts_router = await get_initialized_router(db)

            yield sse_progress(5, "Thompson Sampling 라우터 초기화 완료", "processing")

            # Generate candidates with streaming updates
            n = body.n_candidates
            candidates = []
            scores = []

            yield sse_progress(10, f"{n}개 후보 생성 시작...", "processing")

            # Generate candidates in parallel with progress updates
            async def generate_single(idx: int) -> tuple[int, CandidateResult]:
                candidate = await engine._execute_generation(
                    prompt=body.prompt,
                    app_key=body.app_key,
                    seed=idx * 1000,
                    temperature=0.7 + (idx * 0.3 / n),
                    timeout=30.0,
                )
                return idx, CandidateResult(
                    idx=idx,
                    content=candidate.get("output", ""),
                    metadata={"seed": idx * 1000},
                    latency_ms=0,
                    backend_used=candidate.get("backend_used", "default"),
                )

            # Stream candidate generation
            tasks = [asyncio.create_task(generate_single(i)) for i in range(n)]
            completed = 0

            for coro in asyncio.as_completed(tasks):
                idx, candidate = await coro
                completed += 1
                candidates.append(candidate)

                # Stream candidate result
                progress_pct = 10 + int(40 * completed / n)
                yield sse_event("candidate", {
                    "idx": idx,
                    "content_preview": candidate.content[:200] if candidate.content else "",
                    "backend_used": candidate.backend_used,
                })
                yield sse_progress(progress_pct, f"후보 {completed}/{n} 생성 완료", "processing")

            # Sort candidates by index
            candidates.sort(key=lambda c: c.idx)

            yield sse_progress(55, "품질 평가 시작...", "processing")

            # Evaluate quality with streaming
            for i, candidate in enumerate(candidates):
                score = await evaluator.evaluate(candidate)
                scores.append(score)

                # Stream quality score
                yield sse_event("quality", {
                    "idx": i,
                    "groundedness": round(score.groundedness, 3),
                    "relevance": round(score.relevance, 3),
                    "coherence": round(score.coherence, 3),
                    "creativity": round(score.creativity, 3),
                    "safety": round(score.safety, 3),
                    "weighted_score": round(score.weighted_score, 3),
                })

                progress_pct = 55 + int(25 * (i + 1) / n)
                yield sse_progress(progress_pct, f"후보 {i + 1}/{n} 품질 평가 완료", "processing")

            yield sse_progress(85, "최적 후보 선택 중...", "processing")

            # Select best candidate
            result = await selector.select_best(
                candidates=candidates,
                scores=scores,
                strategy=body.strategy,
            )

            # Stream selection event with Thompson Sampling stats
            arms_stats = {}
            for arm_id in result.arms_used or []:
                arms_stats[arm_id] = ts_router.get_arm_stats(arm_id)

            yield sse_event("selection", {
                "selected_idx": result.selected.idx,
                "method": result.method,
                "confidence": round(result.confidence, 3),
                "arms_used": result.arms_used,
                "arms_stats": arms_stats,
            })

            yield sse_progress(95, "세션 저장 중...", "finalizing")

            # Store session (Redis-backed, 2026 Best Practice)
            prompt_hash = hashlib.sha256(body.prompt.encode()).hexdigest()[:64]
            await _get_session_cache().set(session_id, {
                "candidates": [c.model_dump() for c in candidates],
                "scores": [s.model_dump() for s in scores],
                "prompt_hash": prompt_hash,
                "prompt_preview": body.prompt[:200],
                "app_key": body.app_key,
                "strategy": body.strategy,
                "arms_used": result.arms_used,
                "created_at": datetime.utcnow().isoformat(),
            })

            # Record history (non-blocking)
            try:
                history = SelectionHistory(
                    app_key=body.app_key,
                    prompt_hash=prompt_hash,
                    prompt_preview=body.prompt[:200],
                    n_candidates=len(candidates),
                    candidates_data={"candidates": [c.model_dump() for c in candidates]},
                    quality_scores={"scores": [s.model_dump() for s in scores]},
                    selected_idx=result.selected.idx,
                    selection_method=result.method,
                    selection_confidence=result.confidence,
                    arms_used=result.arms_used,
                    dimension=body.app_key.split(".")[-1] if "." in body.app_key else None,
                )
                db.add(history)
                await db.commit()
            except Exception as e:
                logger.warning(f"History recording failed: {e}")

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Final complete event
            yield sse_complete(
                data={
                    "session_id": session_id,
                    "candidates": [c.model_dump() for c in result.all_candidates],
                    "quality_scores": [s.model_dump() for s in scores],
                    "recommended_idx": result.selected.idx,
                    "method": result.method,
                },
                metrics={
                    "latency_ms": latency_ms,
                    "n_candidates": n,
                    "strategy": body.strategy,
                },
            )

        except asyncio.CancelledError:
            yield sse_error("요청이 취소되었습니다", code="CANCELLED")
        except Exception as e:
            logger.exception(f"UQSL stream error: {e}")
            yield sse_error(f"생성 오류: {type(e).__name__}", code="INTERNAL_ERROR")

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


@router.post("/three-way/stream")
async def three_way_comparison_stream(
    request: ThreeWayComparisonRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    SSE streaming for Ensemble++ 3-way comparison.

    Streams:
    - Individual backend results (A, B)
    - Ensemble merge result (A+B)
    - Thompson Sampling recommendation
    """
    async def stream_three_way() -> AsyncGenerator[str, None]:
        start_time = time.perf_counter()

        try:
            yield sse_progress(1, "Ensemble++ 3-way 비교 시작...", "starting")

            from app.uqsl.ensemble_plus_plus import get_ensemble_router

            ensemble = get_ensemble_router()
            ts_router = await get_initialized_router(db)

            yield sse_progress(10, "Qdrant 검색 중 (옵션 A)...", "processing")

            # Get results in parallel but stream as they complete
            async def get_qdrant_result():
                return await ensemble.get_qdrant_only_result(
                    query=request.query,
                    dimension=request.dimension,
                )

            async def get_notebooklm_result():
                return await ensemble.get_notebooklm_only_result(
                    query=request.query,
                    auteur_key=request.auteur_key,
                )

            results = {}

            # Execute in parallel
            tasks = {
                "a": asyncio.create_task(get_qdrant_result()),
                "b": asyncio.create_task(get_notebooklm_result()),
            }

            for key, task in tasks.items():
                try:
                    result = await task
                    results[key] = result
                    yield sse_event(f"result_{key}", {
                        "option": key.upper(),
                        "source": "qdrant" if key == "a" else "notebooklm",
                        "data": result.model_dump() if result else None,
                    })
                    yield sse_progress(
                        30 if key == "a" else 60,
                        f"옵션 {key.upper()} 완료",
                        "processing",
                    )
                except Exception as e:
                    logger.warning(f"Result {key} failed: {e}")
                    results[key] = None

            yield sse_progress(70, "앙상블 병합 중 (옵션 A+B)...", "processing")

            # Ensemble merge
            try:
                results["ab"] = await ensemble.merge_results(
                    qdrant_result=results.get("a"),
                    notebooklm_result=results.get("b"),
                )
                yield sse_event("result_ab", {
                    "option": "A+B",
                    "source": "ensemble",
                    "data": results["ab"].model_dump() if results["ab"] else None,
                })
            except Exception as e:
                logger.warning(f"Ensemble merge failed: {e}")
                results["ab"] = None

            yield sse_progress(85, "Thompson Sampling 추천 계산 중...", "processing")

            # Get recommendation
            recommended = await ensemble.select_best_arm()

            # Get arm statistics
            arms_stats = {
                "qdrant_only": ts_router.get_arm_stats("backend:qdrant_hybrid"),
                "notebooklm_only": ts_router.get_arm_stats("backend:notebooklm"),
                "ensemble_ab": ts_router.get_arm_stats("ensemble:ab"),
            }

            yield sse_event("recommendation", {
                "recommended": recommended,
                "arms_stats": arms_stats,
            })

            # Record comparison
            try:
                query_hash = hashlib.sha256(request.query.encode()).hexdigest()[:64]
                comparison = EnsembleComparison(
                    query=request.query,
                    query_hash=query_hash,
                    dimension=request.dimension,
                    auteur_key=request.auteur_key,
                    result_a=results["a"].model_dump() if results.get("a") else {},
                    result_b=results["b"].model_dump() if results.get("b") else {},
                    result_ab=results["ab"].model_dump() if results.get("ab") else {},
                    recommended=recommended,
                    arms_stats_before=arms_stats,
                )
                db.add(comparison)
                await db.commit()
            except Exception as e:
                logger.warning(f"Comparison recording failed: {e}")

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            yield sse_complete(
                data={
                    "query": request.query,
                    "results": {
                        "a": results["a"].model_dump() if results.get("a") else None,
                        "b": results["b"].model_dump() if results.get("b") else None,
                        "ab": results["ab"].model_dump() if results.get("ab") else None,
                    },
                    "recommended": recommended,
                    "arms_stats": arms_stats,
                },
                metrics={"latency_ms": latency_ms},
            )

        except asyncio.CancelledError:
            yield sse_error("요청이 취소되었습니다", code="CANCELLED")
        except Exception as e:
            logger.exception(f"Three-way stream error: {e}")
            yield sse_error(f"비교 오류: {type(e).__name__}", code="INTERNAL_ERROR")

    return StreamingResponse(
        stream_three_way(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


@router.post("/select")
async def select_candidate(
    request: SelectBestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    HITL selection endpoint.

    Called when user selects from presented candidates.
    Updates Thompson Sampling arms based on selection.
    """
    session = await _get_session_cache().get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    candidates = session.get("candidates", [])
    if request.selected_idx >= len(candidates):
        raise HTTPException(status_code=400, detail="Invalid candidate index")

    # Update Thompson Sampling for selected arm
    ts_router = await get_initialized_router(db)
    selected = candidates[request.selected_idx]
    backend_used = selected.get("backend_used") if isinstance(selected, dict) else getattr(selected, "backend_used", None)
    if backend_used and backend_used != "default":
        await ts_router.update(db, f"backend:{backend_used}", reward=True)

    # Update non-selected arms
    for i, c in enumerate(candidates):
        c_backend = c.get("backend_used") if isinstance(c, dict) else getattr(c, "backend_used", None)
        if i != request.selected_idx and c_backend and c_backend != "default":
            await ts_router.update(db, f"backend:{c_backend}", reward=False)

    # Update session (Redis-backed)
    await _get_session_cache().update(request.session_id, {
        "selected_idx": request.selected_idx,
        "selection_time": datetime.utcnow().isoformat(),
    })

    return {
        "status": "selected",
        "session_id": request.session_id,
        "selected_idx": request.selected_idx,
    }


@router.post("/feedback")
async def submit_feedback(
    request: SubmitFeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit user feedback for Thompson Sampling updates.

    Positive feedback increases alpha, negative increases beta
    for the arm that generated the selected candidate.
    """
    # Find selection in history
    try:
        selection_uuid = uuid.UUID(request.selection_id)
        result = await db.execute(
            select(SelectionHistory)
            .where(SelectionHistory.id == selection_uuid)
        )
        history = result.scalar_one_or_none()
    except ValueError:
        history = None

    if not history:
        # Try session-based lookup (Redis-backed)
        session = await _get_session_cache().get(request.selection_id)
        if session:
            arms_used = session.get("arms_used", [])
        else:
            # Accept feedback anyway for forward compatibility
            arms_used = []
    else:
        arms_used = history.arms_used or []

    # Update Thompson Sampling
    ts_router = await get_initialized_router(db)
    reward = request.feedback == "positive"

    for arm_id in arms_used:
        await ts_router.update(db, arm_id, reward=reward)

    # Update history record if found
    if history:
        history.user_feedback = request.feedback
        history.feedback_timestamp = datetime.utcnow()
        await db.commit()

    return {
        "status": "recorded",
        "feedback": request.feedback,
        "arms_updated": arms_used,
    }


@router.post("/three-way", response_model=ThreeWayResult)
async def three_way_comparison(
    request: ThreeWayComparisonRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ensemble++ 3-way comparison (NeurIPS 2025).

    Returns results from:
    - A: Qdrant only
    - B: NotebookLM only
    - AB: Ensemble merged
    """
    from app.uqsl.ensemble_plus_plus import get_ensemble_router

    ensemble = get_ensemble_router()
    ts_router = await get_initialized_router(db)

    # Get 3-way results
    results = await ensemble.get_three_way_results(
        query=request.query,
        dimension=request.dimension,
        auteur_key=request.auteur_key,
    )

    # Get recommended option based on Thompson Sampling
    recommended = await ensemble.select_best_arm()

    # Get arm statistics
    arms_stats = {
        "qdrant_only": ts_router.get_arm_stats("backend:qdrant_hybrid"),
        "notebooklm_only": ts_router.get_arm_stats("backend:notebooklm"),
        "ensemble_ab": ts_router.get_arm_stats("ensemble:ab"),
    }

    # Record comparison
    try:
        query_hash = hashlib.sha256(request.query.encode()).hexdigest()[:64]
        comparison = EnsembleComparison(
            query=request.query,
            query_hash=query_hash,
            dimension=request.dimension,
            auteur_key=request.auteur_key,
            result_a=results["a"].model_dump() if results.get("a") else {},
            result_b=results["b"].model_dump() if results.get("b") else {},
            result_ab=results["ab"].model_dump() if results.get("ab") else {},
            recommended=recommended,
            arms_stats_before=arms_stats,
        )
        db.add(comparison)
        await db.commit()
    except Exception:
        pass

    return ThreeWayResult(
        query=request.query,
        results=results,
        recommended=recommended,
        arms_stats=arms_stats,
    )


@router.post("/three-way/select")
async def select_three_way(
    comparison_id: str,
    selected: str,  # "a", "b", "ab", "skip"
    db: AsyncSession = Depends(get_db),
):
    """
    Record user selection from 3-way comparison.

    Updates Thompson Sampling based on selection.
    """
    ts_router = await get_initialized_router(db)

    # Map selection to arm
    arm_map = {
        "a": "backend:qdrant_hybrid",
        "b": "backend:notebooklm",
        "ab": "ensemble:ab",
    }

    if selected in arm_map:
        # Reward selected arm
        await ts_router.update(db, arm_map[selected], reward=True)

        # Penalize non-selected arms
        for key, arm_id in arm_map.items():
            if key != selected:
                await ts_router.update(db, arm_id, reward=False)

    # Update comparison record
    try:
        comparison_uuid = uuid.UUID(comparison_id)
        result = await db.execute(
            select(EnsembleComparison).where(
                EnsembleComparison.id == comparison_uuid
            )
        )
        comparison = result.scalar_one_or_none()
        if comparison:
            comparison.user_selected = selected
            comparison.selection_match = (comparison.recommended == selected)
            comparison.arms_stats_after = ts_router.get_all_stats()
            await db.commit()
    except Exception:
        pass

    return {
        "status": "recorded",
        "selected": selected,
    }


@router.get("/metrics/{app_key}")
async def get_metrics(
    app_key: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get quality metrics for an app.

    Returns aggregated statistics from selection history.
    """
    # Get total selections
    total_result = await db.execute(
        select(func.count(SelectionHistory.id))
        .where(SelectionHistory.app_key == app_key)
    )
    total_selections = total_result.scalar() or 0

    # Get positive rate
    positive_result = await db.execute(
        select(func.count(SelectionHistory.id))
        .where(SelectionHistory.app_key == app_key)
        .where(SelectionHistory.user_feedback == "positive")
    )
    positive_count = positive_result.scalar() or 0

    feedback_result = await db.execute(
        select(func.count(SelectionHistory.id))
        .where(SelectionHistory.app_key == app_key)
        .where(SelectionHistory.user_feedback.isnot(None))
    )
    feedback_count = feedback_result.scalar() or 0

    positive_rate = positive_count / feedback_count if feedback_count > 0 else 0.0

    # Get average quality score (from confidence as proxy)
    avg_result = await db.execute(
        select(func.avg(SelectionHistory.selection_confidence))
        .where(SelectionHistory.app_key == app_key)
    )
    avg_quality_score = avg_result.scalar() or 0.0

    return {
        "app_key": app_key,
        "total_selections": total_selections,
        "positive_rate": round(positive_rate, 3),
        "avg_quality_score": round(float(avg_quality_score), 3),
        "feedback_count": feedback_count,
    }


@router.get("/arms")
async def get_arm_statistics(
    arm_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get Thompson Sampling arm statistics.

    Returns current alpha/beta parameters and success rates.
    """
    ts_router = await get_initialized_router(db)
    stats = ts_router.get_all_stats(arm_type)

    return {
        "arms": stats,
        "total_arms": len(stats),
    }


@router.get("/config/{app_key}")
async def get_config(
    app_key: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get UQSL configuration for an app.
    """
    result = await db.execute(
        select(UQSLConfig).where(UQSLConfig.app_key == app_key)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Return default config
        return {
            "app_key": app_key,
            "n_candidates": 3,
            "selection_strategy": "auto",
            "tier": "free",
            "enabled": True,
            "auto_threshold": 0.85,
            "top_k_for_hitl": 2,
        }

    return {
        "app_key": config.app_key,
        "n_candidates": config.n_candidates,
        "selection_strategy": config.selection_strategy,
        "quality_weights": config.quality_weights,
        "bandit_arms": config.bandit_arms,
        "tier": config.tier,
        "enabled": config.enabled,
        "auto_threshold": config.auto_threshold,
        "top_k_for_hitl": config.top_k_for_hitl,
    }


@router.put("/config/{app_key}")
async def update_config(
    app_key: str,
    n_candidates: Optional[int] = None,
    selection_strategy: Optional[str] = None,
    tier: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Update UQSL configuration for an app.
    """
    result = await db.execute(
        select(UQSLConfig).where(UQSLConfig.app_key == app_key)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Create new config
        config = UQSLConfig(app_key=app_key)
        db.add(config)

    # Update fields
    if n_candidates is not None:
        config.n_candidates = n_candidates
    if selection_strategy is not None:
        config.selection_strategy = selection_strategy
    if tier is not None:
        config.tier = tier
    if enabled is not None:
        config.enabled = enabled

    await db.commit()
    await db.refresh(config)

    return {
        "status": "updated",
        "app_key": config.app_key,
        "n_candidates": config.n_candidates,
        "selection_strategy": config.selection_strategy,
        "tier": config.tier,
        "enabled": config.enabled,
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get UQSL session cache statistics.

    2026 Best Practice: Monitor cache health and performance.
    """
    stats = await _get_session_cache().get_stats()
    return {
        "session_cache": stats,
        "status": "healthy" if stats.get("redis_healthy") else "degraded",
    }
