"""
Health Check Router

Provides system health endpoints for monitoring and load balancer checks.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.utils.error_sanitize import safe_error_detail

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    environment: str
    checks: dict


class ComponentCheck(BaseModel):
    """Individual component health check."""
    status: str
    latency_ms: Optional[float] = None
    message: Optional[str] = None


@router.get("/health", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthStatus:
    """
    Full health check endpoint.
    
    Checks database connectivity and reports system status.
    """
    checks = {}
    overall_status = "healthy"
    
    # Database check
    import time
    start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_latency = (time.perf_counter() - start) * 1000
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency, 2),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = {
            "status": "unhealthy",
            "message": "Database connection failed",
        }
        overall_status = "unhealthy"
    
    # Redis check (optional)
    try:
        from redis.asyncio import from_url as redis_from_url
        redis_url = settings.REDIS_URL
        start = time.perf_counter()
        redis = redis_from_url(redis_url, socket_timeout=2)
        await redis.ping()
        await redis.close()
        redis_latency = (time.perf_counter() - start) * 1000
        checks["redis"] = {
            "status": "healthy",
            "latency_ms": round(redis_latency, 2),
        }
    except Exception as e:
        # Redis is optional, so degraded instead of unhealthy
        logger.debug(f"[Health] Redis check failed: {e}")
        checks["redis"] = {
            "status": "unavailable",
            "message": "Redis not configured or unreachable",
        }
        if overall_status == "healthy":
            overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        checks=checks,
    )


@router.get("/health/live")
async def liveness_probe() -> dict:
    """
    Kubernetes liveness probe.
    
    Simple check that the service is running.
    Always returns 200 if the service is up.
    """
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Kubernetes readiness probe.
    
    Checks if the service is ready to receive traffic.
    Verifies database connectivity.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Not ready: {safe_error_detail(e, 'Readiness check')}")


@router.get("/health/notebooklm")
async def notebooklm_health() -> dict:
    """
    NotebookLM RAG health check.
    
    Reports:
    - Circuit breaker state (closed/open/half-open/degraded)
    - Registry stats (real vs simulation notebooks)
    - Client availability (Playwright, MCP, CircuitBreaker)
    - Cache statistics
    - Auth status (if available)
    """
    try:
        from app.rag.tier0_notebooklm import get_notebooklm_health
        health = get_notebooklm_health()
        
        # Add auth info if available
        try:
            from app.rag.notebooklm_auth import get_auth_service
            auth_service = get_auth_service()
            health["auth"] = auth_service.get_health_dict()
        except Exception:
            health["auth"] = {"status": "unavailable"}
        
        return health
    except Exception as e:
        logger.error(f"NotebookLM health check failed: {e}")
        return {
            "status": "error",
            "message": "NotebookLM unavailable",
        }


@router.get("/health/rag-cache")
async def rag_cache_health() -> dict:
    """
    RAG Cache health check.
    
    Reports:
    - Cache size and max capacity
    - Hit/miss counts and hit rate
    - TTL configuration
    """
    try:
        # === Legacy Cleanup: migrate from get_rag_cache → semantic_cache ===
        from app.rag.semantic_cache import get_semantic_cache
        cache = get_semantic_cache()
        stats = cache.get_stats()
        
        return {
            "status": "healthy",
            "cache_type": "semantic",
            **stats.__dict__,  # CacheStats dataclass
        }
    except Exception as e:
        logger.error(f"RAG cache health check failed: {e}")
        return {
            "status": "error",
            "message": "RAG cache unavailable",
        }


@router.get("/health/uqsl")
async def uqsl_health(db: AsyncSession = Depends(get_db)) -> dict:
    """
    UQSL (Universal Quality Selection Layer) health check.

    Reports:
    - Thompson Sampling router status
    - Active sessions count
    - Metrics collection status
    - Arm statistics summary
    """
    health_data = {
        "status": "healthy",
        "components": {},
    }

    # Check metrics
    try:
        from app.uqsl.metrics import get_uqsl_metrics_summary
        health_data["components"]["metrics"] = get_uqsl_metrics_summary()
    except Exception as e:
        logger.debug(f"UQSL metrics check failed: {e}")
        health_data["components"]["metrics"] = {
            "status": "error",
            "message": "Metrics unavailable",
        }

    # Check Thompson Sampling router
    try:
        from app.uqsl.thompson_sampling import get_initialized_router
        ts_router = await get_initialized_router(db)
        arm_stats = ts_router.get_all_stats()

        total_trials = sum(
            s.get("total_trials", 0)
            for s in arm_stats.values()
        )

        health_data["components"]["thompson_sampling"] = {
            "status": "healthy",
            "total_arms": len(arm_stats),
            "total_trials": total_trials,
            "arms": list(arm_stats.keys()),
        }
    except Exception as e:
        logger.debug(f"Thompson Sampling check failed: {e}")
        health_data["components"]["thompson_sampling"] = {
            "status": "error",
            "message": "Thompson Sampling unavailable",
        }
        health_data["status"] = "degraded"

    # Check active sessions
    try:
        from app.routers.uqsl import _sessions
        session_count = len(_sessions)
        health_data["components"]["sessions"] = {
            "status": "healthy",
            "active_sessions": session_count,
        }
    except Exception as e:
        logger.debug(f"Sessions check failed: {e}")
        health_data["components"]["sessions"] = {
            "status": "unknown",
            "message": "Sessions unavailable",
        }

    # Check Ensemble++ router
    try:
        from app.uqsl.ensemble_plus_plus import get_ensemble_router
        ensemble = get_ensemble_router()
        health_data["components"]["ensemble_plus_plus"] = {
            "status": "healthy",
            "arms": list(ensemble.arms.keys()),
        }
    except Exception as e:
        logger.debug(f"Ensemble++ check failed: {e}")
        health_data["components"]["ensemble_plus_plus"] = {
            "status": "error",
            "message": "Ensemble++ unavailable",
        }
        if health_data["status"] == "healthy":
            health_data["status"] = "degraded"

    return health_data


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.
    Includes DNA Lab metrics:
    - dna_lab_drift_detection_score
    - dna_lab_hitl_review_pending_count
    - dna_lab_transpiler_latency_seconds
    - dna_lab_pipeline_duration_seconds

    Protected by MetricsProtectionMiddleware (IP whitelist or bearer token).
    """
    from fastapi.responses import Response
    from app.metrics import get_metrics

    return Response(
        content=get_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
