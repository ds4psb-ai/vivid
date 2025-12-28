"""Arq Worker for async pipeline processing (Phase 3)."""
import logging
import asyncio
from typing import Any, Dict, List
from arq.connections import RedisSettings
from arq import ArqRedis

from app.config import Settings
from app.notebooklm_client import run_notebooklm_analysis
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
    Run NotebookLM-style analysis on a source pack.
    
    Args:
        source_pack: Source pack data with segment_refs.
        capsule_id: Target capsule ID for style context.
    
    Returns:
        Analysis result dict with summary and evidence_refs.
    """
    logger.info(f"[Job] analyze_source_pack: capsule_id={capsule_id}")
    try:
        summary, evidence_refs = run_notebooklm_analysis(source_pack, capsule_id)
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


class WorkerSettings:
    """Arq WorkerSettings for job processing."""
    functions = [analyze_source_pack, generate_video_batch]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    handle_signals = False
    job_timeout = 600  # 10 minutes max per job
 
