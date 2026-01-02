"""Sandbox API Router.

Endpoints for sandboxed tool execution:
- Execute tool in sandbox
- Get execution status/results
- List executions
- Manage sandbox configs (admin)
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models_sandbox import SandboxConfig, SandboxExecution, ExecutionStatus
from app.models_telemetry import ToolManifest
from app.services import sandbox_executor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sandbox", tags=["Sandbox"])


# =============================================================================
# Schemas
# =============================================================================

class ExecuteRequest(BaseModel):
    """Request to execute tool in sandbox."""
    tool_id: UUID
    input_data: dict = Field(default_factory=dict)
    session_id: Optional[str] = None


class ExecutionResponse(BaseModel):
    """Execution result response."""
    id: UUID
    tool_id: UUID
    status: str
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: Optional[int] = None
    credits_charged: int = 0
    credits_refunded: int = 0

    class Config:
        from_attributes = True


class ExecutionDetail(BaseModel):
    """Detailed execution response."""
    id: UUID
    tool_id: UUID
    version_id: Optional[UUID]
    config_id: UUID
    user_id: str
    status: str
    input_data: dict
    output_data: Optional[dict]
    error_message: Optional[str]
    error_code: Optional[str]
    execution_time_ms: Optional[int]
    memory_used_mb: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    exit_code: Optional[int]
    queued_at: str
    started_at: Optional[str]
    finished_at: Optional[str]
    credits_charged: int
    credits_refunded: int


class SandboxConfigResponse(BaseModel):
    """Sandbox config response."""
    id: UUID
    name: str
    tier: str
    timeout_seconds: int
    memory_mb: int
    cpu_limit: float
    network_enabled: bool
    filesystem_readonly: bool


# =============================================================================
# Execution Endpoints
# =============================================================================

@router.post("/execute", response_model=ExecutionResponse)
async def execute_tool(
    request: ExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Execute a tool in sandbox environment.
    
    The tool will be executed with resource limits based on its tier:
    - experimental: strict isolation, no network, 30s timeout
    - verified: standard isolation, limited network, 60s timeout
    - certified: trusted mode, full network, 120s timeout
    """
    try:
        execution, result = await sandbox_executor.execute_tool_sandboxed(
            db=db,
            tool_id=request.tool_id,
            input_data=request.input_data,
            user_id=current_user["id"],
            session_id=request.session_id,
        )
        
        return ExecutionResponse(
            id=execution.id,
            tool_id=execution.tool_id,
            status=execution.status,
            output_data=execution.output_data,
            error_message=execution.error_message,
            error_code=execution.error_code,
            execution_time_ms=execution.execution_time_ms,
            credits_charged=execution.credits_charged,
            credits_refunded=execution.credits_refunded,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Sandbox execution failed: {e}")
        raise HTTPException(status_code=500, detail="Execution failed")


@router.get("/executions/{execution_id}", response_model=ExecutionDetail)
async def get_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get execution details."""
    execution = await db.get(SandboxExecution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # Only owner or admin can view
    if execution.user_id != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ExecutionDetail(
        id=execution.id,
        tool_id=execution.tool_id,
        version_id=execution.version_id,
        config_id=execution.config_id,
        user_id=execution.user_id,
        status=execution.status,
        input_data=execution.input_data,
        output_data=execution.output_data,
        error_message=execution.error_message,
        error_code=execution.error_code,
        execution_time_ms=execution.execution_time_ms,
        memory_used_mb=execution.memory_used_mb,
        stdout=execution.stdout,
        stderr=execution.stderr,
        exit_code=execution.exit_code,
        queued_at=execution.queued_at.isoformat(),
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        finished_at=execution.finished_at.isoformat() if execution.finished_at else None,
        credits_charged=execution.credits_charged,
        credits_refunded=execution.credits_refunded,
    )


@router.get("/executions", response_model=list[ExecutionResponse])
async def list_my_executions(
    tool_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List my sandbox executions."""
    query = (
        select(SandboxExecution)
        .where(SandboxExecution.user_id == current_user["id"])
    )
    
    if tool_id:
        query = query.where(SandboxExecution.tool_id == tool_id)
    if status:
        query = query.where(SandboxExecution.status == status)
    
    query = query.order_by(SandboxExecution.queued_at.desc()).limit(limit)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return [
        ExecutionResponse(
            id=e.id,
            tool_id=e.tool_id,
            status=e.status,
            output_data=e.output_data,
            error_message=e.error_message,
            error_code=e.error_code,
            execution_time_ms=e.execution_time_ms,
            credits_charged=e.credits_charged,
            credits_refunded=e.credits_refunded,
        )
        for e in executions
    ]


# =============================================================================
# Admin Endpoints
# =============================================================================

@router.get("/stats")
async def sandbox_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get sandbox execution statistics (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Count by status
    status_counts = {}
    for status in ExecutionStatus:
        count = await db.execute(
            select(func.count())
            .where(SandboxExecution.status == status.value)
        )
        status_counts[status.value] = count.scalar() or 0
    
    # Average execution time
    avg_time = await db.execute(
        select(func.avg(SandboxExecution.execution_time_ms))
        .where(SandboxExecution.status == ExecutionStatus.SUCCESS.value)
    )
    
    # Total executions today
    from datetime import datetime
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db.execute(
        select(func.count())
        .where(SandboxExecution.queued_at >= today)
    )
    
    return {
        "status_counts": status_counts,
        "avg_execution_time_ms": round(avg_time.scalar() or 0, 1),
        "executions_today": today_count.scalar() or 0,
    }


@router.get("/configs", response_model=list[SandboxConfigResponse])
async def list_configs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List sandbox configurations (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = await db.execute(
        select(SandboxConfig).where(SandboxConfig.is_active == True)
    )
    configs = result.scalars().all()
    
    return [
        SandboxConfigResponse(
            id=c.id,
            name=c.name,
            tier=c.tier,
            timeout_seconds=c.timeout_seconds,
            memory_mb=c.memory_mb,
            cpu_limit=c.cpu_limit,
            network_enabled=c.network_enabled,
            filesystem_readonly=c.filesystem_readonly,
        )
        for c in configs
    ]


@router.post("/configs/seed")
async def seed_default_configs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Seed default sandbox configurations (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    created = 0
    for tier in ["strict", "standard", "trusted"]:
        config = await sandbox_executor.get_or_create_default_config(db, tier)
        if config:
            created += 1
    
    return {"message": f"Created/verified {created} configs"}
