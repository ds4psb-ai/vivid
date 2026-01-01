"""
Health Check Router

Provides system health endpoints for monitoring and load balancer checks.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

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
        checks["database"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        overall_status = "unhealthy"
    
    # Redis check (optional)
    try:
        import aioredis
        redis_url = settings.REDIS_URL
        start = time.perf_counter()
        redis = await aioredis.from_url(redis_url, socket_timeout=2)
        await redis.ping()
        await redis.close()
        redis_latency = (time.perf_counter() - start) * 1000
        checks["redis"] = {
            "status": "healthy",
            "latency_ms": round(redis_latency, 2),
        }
    except Exception:
        # Redis is optional, so degraded instead of unhealthy
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
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")
