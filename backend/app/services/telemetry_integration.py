"""Telemetry Integration Helper.

Provides helper functions to integrate telemetry and settlement
into existing code paths with minimal refactoring.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_telemetry import ToolManifest, ToolRunEvent

logger = logging.getLogger(__name__)


async def get_tool_by_key(db: AsyncSession, tool_key: str) -> Optional[ToolManifest]:
    """Get tool manifest by key."""
    result = await db.execute(
        select(ToolManifest).where(ToolManifest.tool_key == tool_key)
    )
    return result.scalars().first()


async def record_tool_run(
    db: AsyncSession,
    tool_key: str,
    user_id: str,
    inputs_summary: Dict[str, Any],
    outputs_summary: Dict[str, Any],
    status: str,
    latency_ms: int,
    credits_charged: int,
    error_message: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Optional[ToolRunEvent]:
    """
    Record a tool run event and trigger settlement if successful.
    
    This is the main integration point for existing endpoints.
    Call this after tool execution completes.
    
    Args:
        db: Database session
        tool_key: e.g. "generate_veo_prompt"
        user_id: User who ran the tool
        inputs_summary: Sanitized inputs (no PII)
        outputs_summary: Result summary
        status: "success", "failed", "error"
        latency_ms: Execution time
        credits_charged: Credits deducted
        error_message: Error if failed
        session_id: Optional session for grouping
    
    Returns:
        ToolRunEvent if created, None if tool not found or error
    """
    try:
        # Validate inputs
        if not tool_key or not user_id:
            logger.warning(f"record_tool_run: missing tool_key or user_id")
            return None
        
        # Ensure non-negative values
        latency_ms = max(0, latency_ms or 0)
        credits_charged = max(0, credits_charged or 0)
        
        # Get tool from DB
        tool = await get_tool_by_key(db, tool_key)
        
        if not tool:
            # Tool not in DB yet - log but don't fail
            logger.debug(f"Tool {tool_key} not in DB, skipping telemetry")
            return None
        
        # Parse session_id if string UUID
        parsed_session_id = None
        if session_id:
            try:
                if isinstance(session_id, str):
                    parsed_session_id = UUID(session_id) if len(session_id) == 36 else None
                else:
                    parsed_session_id = session_id
            except (ValueError, TypeError):
                parsed_session_id = None
        
        # Create run event
        run_event = ToolRunEvent(
            id=uuid4(),
            tool_id=tool.id,
            tool_key=tool_key,
            tool_version=tool.version or "1.0.0",
            user_id=user_id,
            session_id=parsed_session_id,
            status=status,
            inputs_summary=_sanitize_inputs(inputs_summary or {}),
            outputs_summary=_truncate_outputs(outputs_summary or {}),
            error_message=error_message[:500] if error_message else None,
            latency_ms=latency_ms,
            credits_charged=credits_charged,
            credits_refunded=0,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if status in ["success", "failed"] else None,
        )
        
        db.add(run_event)
        
        # Update tool usage count (with null safety)
        tool.usage_count = (tool.usage_count or 0) + 1
        
        await db.commit()
        await db.refresh(run_event)
        
        logger.info(
            f"Tool run recorded: {tool_key}, status={status}, "
            f"latency={latency_ms}ms, credits={credits_charged}"
        )
        
        # If successful, create settlement (async, don't block)
        if status == "success" and credits_charged > 0:
            try:
                await _create_settlement_for_run(db, run_event, tool, user_id)
            except Exception as e:
                # Log but don't fail the main request
                logger.error(f"Settlement creation failed: {e}")
        
        return run_event
        
    except Exception as e:
        # Never let telemetry failures break the main request
        logger.error(f"record_tool_run failed for {tool_key}: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
        return None


async def update_run_feedback(
    db: AsyncSession,
    run_id: UUID,
    user_id: str,
    rating: Optional[int] = None,
    feedback: Optional[str] = None,
) -> bool:
    """Update run with user feedback."""
    run = await db.get(ToolRunEvent, run_id)
    if not run:
        return False
    
    # Only owner can give feedback
    if run.user_id != user_id:
        return False
    
    if rating is not None:
        run.user_rating = rating
    if feedback is not None:
        run.user_feedback = feedback[:500]
    
    await db.commit()
    return True


def _sanitize_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Remove PII from inputs before storing."""
    sanitized = {}
    # Only keep non-sensitive fields
    safe_keys = {"topic", "style", "mood", "duration", "language", "model",
                 "concept", "scene_count", "description", "aspect_ratio",
                 "focus_areas", "prompt"}
    
    for key, value in inputs.items():
        if key in safe_keys:
            if isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
    
    return sanitized


def _truncate_outputs(outputs: Dict[str, Any]) -> Dict[str, Any]:
    """Truncate outputs to reasonable size."""
    truncated = {}
    for key, value in outputs.items():
        if isinstance(value, str) and len(value) > 500:
            truncated[key] = value[:500] + "..."
        elif isinstance(value, list) and len(value) > 10:
            truncated[key] = value[:10]
        else:
            truncated[key] = value
    
    return truncated


async def _create_settlement_for_run(
    db: AsyncSession,
    run_event: ToolRunEvent,
    tool: ToolManifest,
    payer_user_id: str,
) -> None:
    """Create settlement for a successful tool run."""
    from app.services.fork_revenue_service import create_settlement
    
    await create_settlement(
        db=db,
        tool_run_id=run_event.id,
        tool_id=tool.id,
        tool_key=tool.tool_key,
        total_credits=run_event.credits_charged,
        payer_user_id=payer_user_id,
    )
    
    logger.info(f"Settlement created for run {run_event.id}")
