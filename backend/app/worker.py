"""Arq Worker for async pipeline processing (Phase 3)."""
import logging
import asyncio
from typing import Any, Dict, List
from arq.connections import RedisSettings
from arq import ArqRedis

from app.config import Settings
from app.gemini_analysis_client import run_gemini_analysis
from app.generation_client import run_generation_pipeline, GenProvider

settings = Settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def startup(ctx: Any) -> None:
    """Worker startup: Initialize any shared resources."""
    logger.info("Worker starting up...")
    # Future: Initialize DB session pool if needed
    # ctx["db"] = await create_pool(...)


async def shutdown(ctx: Any) -> None:
    """Worker shutdown: Cleanup resources."""
    logger.info("Worker shutting down...")


# ─────────────────────────────────────────────────────────────────────────────
# Job Definitions
# ─────────────────────────────────────────────────────────────────────────────

async def analyze_source_pack(
    ctx: Dict[str, Any],
    source_pack: Dict[str, Any],
    capsule_id: str,
) -> Dict[str, Any]:
    """
    Run Gemini analysis on a source pack (NotebookLM-style).
    
    Args:
        source_pack: Source pack data with segment_refs.
        capsule_id: Target capsule ID for style context.
    
    Returns:
        Analysis result dict with summary and evidence_refs.
    """
    logger.info(f"[Job] analyze_source_pack: capsule_id={capsule_id}")
    try:
        summary, evidence_refs = run_gemini_analysis(source_pack, capsule_id)
        return {
            "status": "completed",
            "capsule_id": capsule_id,
            "summary": summary,
            "evidence_refs": evidence_refs,
        }
    except Exception as e:
        logger.exception(f"analyze_source_pack failed: {e}")
        return {"status": "failed", "error": str(e)}


async def generate_video_batch(
    ctx: Dict[str, Any],
    storyboard_cards: List[Dict[str, Any]],
    provider: str = "mock",
    sequence_id: str = "seq-01",
    scene_id: str = "scene-01",
) -> Dict[str, Any]:
    """
    Run video generation pipeline from storyboard cards.
    
    Args:
        storyboard_cards: List of storyboard card dicts.
        provider: Gen provider (mock, veo, kling).
        sequence_id: Sequence identifier.
        scene_id: Scene identifier.
    
    Returns:
        Generation results and metrics.
    """
    logger.info(f"[Job] generate_video_batch: {len(storyboard_cards)} cards, provider={provider}")
    try:
        gen_provider = GenProvider(provider)
        results, metrics = await run_generation_pipeline(
            storyboard_cards,
            provider=gen_provider,
            sequence_id=sequence_id,
            scene_id=scene_id,
        )
        return {
            "status": "completed",
            "results": [r.__dict__ for r in results],
            "metrics": metrics,
        }
    except Exception as e:
        logger.exception(f"generate_video_batch failed: {e}")
        return {"status": "failed", "error": str(e)}


async def sandbox_execute(
    ctx: Dict[str, Any],
    tool_id: str,
    input_data: Dict[str, Any],
    user_id: str,
    session_id: str = None,
) -> Dict[str, Any]:
    """
    Execute a tool in sandbox asynchronously.
    
    Args:
        tool_id: Tool UUID as string.
        input_data: Tool input parameters.
        user_id: User triggering execution.
        session_id: Optional session ID.
    
    Returns:
        Execution result dict.
    """
    from uuid import UUID
    from app.database import AsyncSessionLocal
    from app.services.sandbox_executor import execute_tool_sandboxed
    
    logger.info(f"[Job] sandbox_execute: tool_id={tool_id}, user_id={user_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            execution, result = await execute_tool_sandboxed(
                db=db,
                tool_id=UUID(tool_id),
                input_data=input_data,
                user_id=user_id,
                session_id=session_id,
            )
            
            return {
                "status": "completed",
                "execution_id": str(execution.id),
                "execution_status": execution.status,
                "output": result.output,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
            }
    except Exception as e:
        logger.exception(f"sandbox_execute failed: {e}")
async def index_tool(
    ctx: Dict[str, Any],
    tool_id: str,
) -> Dict[str, Any]:
    """
    Index a tool in the vector database.
    Called when a tool is created or updated.
    
    Args:
        tool_id: Tool UUID as string.
    
    Returns:
        Indexing result.
    """
    from uuid import UUID
    from app.database import AsyncSessionLocal
    from app.models import Tool
    from app.services.vector_service import get_vector_service
    from sqlalchemy import select
    
    logger.info(f"[Job] index_tool: tool_id={tool_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Tool).where(Tool.id == UUID(tool_id))
            )
            tool = result.scalar_one_or_none()
            
            if not tool:
                return {"status": "failed", "error": "Tool not found"}
            
            service = get_vector_service()
            success = service.index_tool({
                "id": str(tool.id),
                "tool_key": tool.tool_key,
                "display_name": tool.display_name,
                "description": tool.description,
                "category": tool.category,
                "tier": tool.tier,
                "usage_count": tool.usage_count,
                "quality_rating": tool.quality_rating,
                "input_schema": tool.input_schema,
            })
            
            return {
                "status": "completed" if success else "failed",
                "tool_id": tool_id,
                "indexed": success,
            }
    except Exception as e:
        logger.exception(f"index_tool failed: {e}")
        return {"status": "failed", "error": str(e)}


async def poll_batch_jobs(
    ctx: Dict[str, Any],
    job_ids: List[str] = None,
) -> Dict[str, Any]:
    """
    Poll batch job statuses and handle completions.
    
    This job runs periodically to:
    1. Check status of pending/running batch jobs
    2. Trigger callbacks for completed jobs
    3. Clean up old completed jobs
    
    Args:
        job_ids: Optional list of specific job IDs to poll.
                 If None, polls all pending/running jobs.
    
    Returns:
        Summary of polled jobs and their statuses.
    """
    from app.services.batch_processor import (
        BatchProcessor,
        BatchJobStatus,
    )
    
    logger.info(f"[Job] poll_batch_jobs: job_ids={job_ids}")
    
    try:
        # Get jobs to poll
        if job_ids:
            jobs_to_poll = [
                await BatchProcessor.get_job_status(job_id)
                for job_id in job_ids
            ]
            jobs_to_poll = [j for j in jobs_to_poll if j is not None]
        else:
            # Poll all pending/running jobs
            pending_jobs = await BatchProcessor.list_jobs(status=BatchJobStatus.PENDING)
            running_jobs = await BatchProcessor.list_jobs(status=BatchJobStatus.RUNNING)
            jobs_to_poll = pending_jobs + running_jobs
        
        results = {
            "polled": 0,
            "completed": 0,
            "failed": 0,
            "still_running": 0,
            "job_statuses": {},
        }
        
        for job in jobs_to_poll:
            results["polled"] += 1
            
            # Get updated status
            updated_job = await BatchProcessor.get_job_status(job.job_id)
            if not updated_job:
                continue
            
            status = updated_job.status
            results["job_statuses"][job.job_id] = status.value
            
            if status == BatchJobStatus.SUCCEEDED:
                results["completed"] += 1
                # TODO: Trigger callback if configured
                callback_url = (updated_job.metadata or {}).get("callback_url")
                if callback_url:
                    logger.info(f"Would trigger callback for {job.job_id}: {callback_url}")
                    
            elif status == BatchJobStatus.FAILED:
                results["failed"] += 1
                logger.warning(
                    f"Batch job failed: {job.job_id}",
                    extra={"error": updated_job.error}
                )
                
            elif status in [BatchJobStatus.PENDING, BatchJobStatus.RUNNING]:
                results["still_running"] += 1
        
        logger.info(f"[Job] poll_batch_jobs completed: {results}")
        return {"status": "completed", **results}
        
    except Exception as e:
        logger.exception(f"poll_batch_jobs failed: {e}")
        return {"status": "failed", "error": str(e)}


async def process_pending_settlements(
    ctx: Dict[str, Any],
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Process pending settlements in batch.
    
    This cron job runs every 5 minutes to:
    1. Find all pending settlements
    2. Process each one (credit payouts)
    3. Update status to completed or failed
    
    Args:
        limit: Max settlements to process per run.
    
    Returns:
        Summary of processed settlements.
    """
    from app.database import AsyncSessionLocal
    from app.services.fork_revenue_service import process_batch_settlements
    
    logger.info(f"[Cron] process_pending_settlements: limit={limit}")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await process_batch_settlements(
                db=db,
                limit=limit,
                processed_by="cron:settlement_worker",
            )
            
            logger.info(
                f"[Cron] Settlement batch complete: "
                f"processed={result['processed']}, "
                f"succeeded={result['succeeded']}, "
                f"failed={result['failed']}"
            )
            
            return {
                "status": "completed",
                **result,
            }
    except Exception as e:
        logger.exception(f"process_pending_settlements failed: {e}")
        return {"status": "failed", "error": str(e)}


async def check_tier_promotions(
    ctx: Dict[str, Any],
    auto_promote: bool = True,
) -> Dict[str, Any]:
    """
    Check and optionally auto-promote tools to higher tiers.
    
    This cron job runs daily to:
    1. Evaluate all tools for tier promotion
    2. Optionally auto-promote eligible tools
    
    Args:
        auto_promote: If True, automatically promote eligible tools.
    
    Returns:
        Summary of promotion checks.
    """
    from app.database import AsyncSessionLocal
    from app.services.telemetry_service import check_all_tier_promotions
    
    logger.info(f"[Cron] check_tier_promotions: auto_promote={auto_promote}")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await check_all_tier_promotions(
                db=db,
                auto_promote=auto_promote,
            )
            
            logger.info(
                f"[Cron] Tier check complete: "
                f"checked={result['checked']}, "
                f"promoted={result['promoted']}"
            )
            
            return {
                "status": "completed",
                **result,
            }
    except Exception as e:
        logger.exception(f"check_tier_promotions failed: {e}")
        return {"status": "failed", "error": str(e)}


async def process_ip_payout_holdbacks(
    ctx: Dict[str, Any],
    limit: int = 200,
) -> Dict[str, Any]:
    """Release IP payout holdbacks once the holdback window expires."""
    from app.database import AsyncSessionLocal
    from app.services.ip_payout_service import release_due_holdbacks

    logger.info(f"[Cron] process_ip_payout_holdbacks: limit={limit}")

    try:
        async with AsyncSessionLocal() as db:
            result = await release_due_holdbacks(
                db=db,
                limit=limit,
                processed_by="cron:ip_payout_holdbacks",
            )

            logger.info(
                f"[Cron] IP payout holdbacks released: processed={result['processed']}, "
                f"released={result['released']}"
            )

            return {"status": "completed", **result}
    except Exception as e:
        logger.exception(f"process_ip_payout_holdbacks failed: {e}")
        return {"status": "failed", "error": str(e)}


async def run_daily_learning_cycle(
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run daily feedback → RAG learning cycle.

    This cron job runs daily at 2 AM UTC to:
    1. Collect unprocessed feedback events
    2. Process positive feedback (rating >= 4) → Qdrant indexing
    3. Process negative feedback → corrections
    4. Update rag_presets confidence scores

    Returns:
        Summary of learning cycle.
    """
    from datetime import datetime
    from app.database import AsyncSessionLocal
    from app.services.feedback_loop import FeedbackLoopService

    cycle_id = f"cycle_{datetime.utcnow().strftime('%Y-%m-%d')}"
    logger.info(f"[Cron] run_daily_learning_cycle: {cycle_id}")

    try:
        async with AsyncSessionLocal() as db:
            service = FeedbackLoopService(db)
            result = await service.aggregate_learning_cycle(cycle_id)
            await db.commit()

            logger.info(
                f"[Cron] Learning cycle complete: {cycle_id} | "
                f"ingested={result.ingested_count}, corrected={result.corrected_count}"
            )

            return {
                "status": "completed",
                "cycle_id": result.cycle_id,
                "processed": result.processed_count,
                "ingested": result.ingested_count,
                "corrected": result.corrected_count,
                "errors": result.error_count,
                "duration_seconds": result.duration_seconds,
            }
    except Exception as e:
        logger.exception(f"run_daily_learning_cycle failed: {e}")
        return {"status": "failed", "error": str(e)}


async def process_expired_approval_checkpoints(
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process expired approval gate checkpoints.

    This cron job runs every hour to handle checkpoints that have expired
    without receiving a review decision.

    Returns:
        Summary of processed checkpoints.
    """
    from app.database import AsyncSessionLocal
    from app.services.approval_gate import ApprovalGateService

    logger.info("[Cron] process_expired_approval_checkpoints")

    try:
        async with AsyncSessionLocal() as db:
            service = ApprovalGateService(db)
            processed_count = await service.process_expired_checkpoints()
            await db.commit()

            logger.info(
                f"[Cron] Expired checkpoints processed: {processed_count}"
            )

            return {
                "status": "completed",
                "processed": processed_count,
            }
    except Exception as e:
        logger.exception(f"process_expired_approval_checkpoints failed: {e}")
        return {"status": "failed", "error": str(e)}


async def poll_outbox(
    ctx: Dict[str, Any],
    batch_size: int = 100,
) -> Dict[str, Any]:
    """
    Poll and publish outbox events to Qdrant.

    This cron job runs every minute to:
    1. Fetch pending outbox events
    2. Publish them to external systems (Qdrant)
    3. Mark as published or schedule retry on failure

    Args:
        batch_size: Maximum events to process per poll

    Returns:
        Summary of published events.
    """
    from app.database import AsyncSessionLocal
    from app.services.outbox_publisher import OutboxPublisher

    logger.info(f"[Cron] poll_outbox: batch_size={batch_size}")

    try:
        publisher = OutboxPublisher(batch_size=batch_size)
        async with AsyncSessionLocal() as db:
            published_count = await publisher.poll_and_publish(db)

            logger.info(f"[Cron] Outbox poll complete: published={published_count}")

            return {
                "status": "completed",
                "published": published_count,
            }
    except Exception as e:
        logger.exception(f"poll_outbox failed: {e}")
        return {"status": "failed", "error": str(e)}


async def run_drift_detection(
    ctx: Dict[str, Any],
    auteur_keys: List[str] = None,
) -> Dict[str, Any]:
    """
    Run periodic drift detection for Logic Vectors.

    This cron job runs every 6 hours to:
    1. Get all active auteur keys (or specified subset)
    2. Run detect_drift() for each
    3. Queue high-drift items for HITL review
    4. Record metrics for monitoring

    Args:
        ctx: Arq context
        auteur_keys: Optional list of specific auteurs to check.

    Returns:
        Summary of drift detection results.
    """
    import time
    from app.database import AsyncSessionLocal
    from app.services.logic_vector_versioning import LogicVectorVersioning, DRIFT_THRESHOLD
    from app.schemas.drift_detection import DriftAction
    from app.metrics import record_drift_score, record_drift_detection

    logger.info(f"[Cron] run_drift_detection: auteurs={auteur_keys}")

    try:
        async with AsyncSessionLocal() as db:
            service = LogicVectorVersioning()

            # Get auteur keys to check
            if not auteur_keys:
                auteur_keys = await service.get_active_auteur_keys(db)

            if not auteur_keys:
                logger.info("[Cron] No active auteur keys found for drift detection")
                return {
                    "status": "completed",
                    "checked": 0,
                    "message": "No active auteur keys found",
                }

            results = {
                "checked": 0,
                "drifted": 0,
                "queued_for_review": 0,
                "auto_upgraded": 0,
                "details": {},
            }

            for auteur_key in auteur_keys:
                start_time = time.time()
                try:
                    # Use auteur_key as ip_id (or construct proper ip_id)
                    ip_id = f"auteur:{auteur_key}"

                    # Detect drift (without new videos - checks current state)
                    drift_result = await service.detect_drift(
                        ip_id=ip_id,
                        new_videos=[],  # Empty = check current version only
                        db=db,
                    )

                    duration = time.time() - start_time
                    results["checked"] += 1

                    # Record metrics
                    record_drift_score(auteur_key, drift_result.drift_score)
                    record_drift_detection(
                        auteur_key,
                        drift_result.action.value if drift_result.action else "NO_CHANGE",
                        duration,
                    )

                    results["details"][auteur_key] = {
                        "drift_score": drift_result.drift_score,
                        "action": drift_result.action.value if drift_result.action else None,
                        "duration_seconds": round(duration, 2),
                    }

                    if drift_result.drift_score > DRIFT_THRESHOLD:
                        results["drifted"] += 1

                    if drift_result.action == DriftAction.REQUIRE_HUMAN_REVIEW:
                        results["queued_for_review"] += 1

                    if drift_result.action == DriftAction.AUTO_UPGRADE:
                        results["auto_upgraded"] += 1

                except Exception as e:
                    logger.warning(f"[Cron] Drift detection failed for {auteur_key}: {e}")
                    results["details"][auteur_key] = {
                        "error": str(e),
                    }

            await db.commit()

            logger.info(
                f"[Cron] Drift detection complete: checked={results['checked']}, "
                f"drifted={results['drifted']}, queued={results['queued_for_review']}"
            )
            return {"status": "completed", **results}

    except Exception as e:
        logger.exception(f"run_drift_detection failed: {e}")
        return {"status": "failed", "error": str(e)}


async def analyze_feedback_weekly(
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run weekly feedback analysis.

    This cron job runs every Sunday at 03:00 UTC to:
    1. Detect failure patterns in DNA Lab pipeline
    2. Detect low-rating patterns
    3. Generate improvement recommendations
    4. Notify admin on critical patterns

    Returns:
        Summary of analysis including pattern counts.
    """
    from app.database import AsyncSessionLocal
    from app.services.feedback_analyzer import FeedbackAnalyzer

    logger.info("[Cron] analyze_feedback_weekly")

    try:
        analyzer = FeedbackAnalyzer()
        async with AsyncSessionLocal() as db:
            summary = await analyzer.analyze_weekly(db)
            await db.commit()

            logger.info(
                f"[Cron] Weekly feedback analysis complete: "
                f"total_runs={summary.total_runs}, "
                f"failure_patterns={len(summary.failure_patterns)}, "
                f"recommendations={len(summary.recommendations)}"
            )

            return {
                "status": "completed",
                "period_start": summary.period_start.isoformat(),
                "period_end": summary.period_end.isoformat(),
                "total_runs": summary.total_runs,
                "success_count": summary.success_count,
                "failure_count": summary.failure_count,
                "patterns": len(summary.failure_patterns),
                "recommendations": len(summary.recommendations),
            }
    except Exception as e:
        logger.exception(f"analyze_feedback_weekly failed: {e}")
        return {"status": "failed", "error": str(e)}


class WorkerSettings:
    """Arq WorkerSettings for job processing."""
    functions = [
        analyze_source_pack,
        generate_video_batch,
        sandbox_execute,
        index_tool,
        poll_batch_jobs,
        process_pending_settlements,
        check_tier_promotions,
        process_ip_payout_holdbacks,
        run_daily_learning_cycle,
        process_expired_approval_checkpoints,
        poll_outbox,
        analyze_feedback_weekly,
        run_drift_detection,
    ]

    # Cron jobs - scheduled tasks
    cron_jobs = [
        # Process settlements every 5 minutes
        {
            "func": process_pending_settlements,
            "cron": "*/5 * * * *",  # Every 5 minutes
            "unique": True,
        },
        # Check tier promotions daily at 2 AM
        {
            "func": check_tier_promotions,
            "cron": "0 2 * * *",  # 2:00 AM daily
            "unique": True,
        },
        # Release IP payout holdbacks daily at 3 AM
        {
            "func": process_ip_payout_holdbacks,
            "cron": "0 3 * * *",  # 3:00 AM daily
            "unique": True,
        },
        # Run daily learning cycle at 2 AM UTC (Phase 7)
        {
            "func": run_daily_learning_cycle,
            "cron": "0 2 * * *",  # 2:00 AM daily
            "unique": True,
        },
        # Process expired approval checkpoints every hour (Phase 7)
        {
            "func": process_expired_approval_checkpoints,
            "cron": "0 * * * *",  # Every hour
            "unique": True,
        },
        # Poll outbox for Qdrant sync every minute (DNA Lab P0)
        {
            "func": poll_outbox,
            "cron": "*/1 * * * *",  # Every minute
            "unique": True,
        },
        # Weekly feedback analysis on Sunday at 3 AM UTC (DNA Lab P0)
        {
            "func": analyze_feedback_weekly,
            "cron": "0 3 * * 0",  # Sunday 03:00 UTC
            "unique": True,
        },
        # Drift detection every 6 hours (DNA Lab P1)
        {
            "func": run_drift_detection,
            "cron": "0 */6 * * *",  # Every 6 hours at minute 0
            "unique": True,
        },
    ]
    
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    handle_signals = False
    job_timeout = 600  # 10 minutes max per job
