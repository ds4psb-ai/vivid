"""Dead Letter Queue Service.

Provides functions to:
- Add failed operations to DLQ
- List and filter DLQ items
- Retry/resolve DLQ items
- Dashboard statistics
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_dlq import DeadLetterQueueItem, DLQEventType, DLQStatus

logger = logging.getLogger(__name__)


# =============================================================================
# DLQ Creation
# =============================================================================

async def add_to_dlq(
    db: AsyncSession,
    event_type: DLQEventType,
    user_id: str,
    operation_type: str,
    error_message: str,
    amount: int = 0,
    error_type: Optional[str] = None,
    stack_trace: Optional[str] = None,
    original_payload: Optional[dict] = None,
) -> DeadLetterQueueItem:
    """
    Add a failed operation to the Dead Letter Queue.
    
    Args:
        db: Database session
        event_type: Type of event (refund_failed, settlement_failed, etc.)
        user_id: Affected user ID
        operation_type: What operation was being performed
        error_message: Error message
        amount: Credits amount involved (for refunds)
        error_type: Exception type name
        stack_trace: Full stack trace if available
        original_payload: Original request/context data
    
    Returns:
        Created DLQ item
    """
    try:
        # Validate inputs
        if not user_id:
            user_id = "unknown"
        if not operation_type:
            operation_type = "unknown"
        
        # Ensure amount is non-negative
        amount = max(0, amount or 0)
        
        item = DeadLetterQueueItem(
            id=uuid4(),
            event_type=event_type.value,
            status=DLQStatus.PENDING.value,
            user_id=user_id[:255],  # Truncate to column limit
            operation_type=operation_type[:100],
            amount=amount,
            error_message=(error_message or "Unknown error")[:2000],
            error_type=error_type[:100] if error_type else None,
            stack_trace=stack_trace[:5000] if stack_trace else None,
            original_payload=original_payload or {},
        )
        
        db.add(item)
        await db.commit()
        await db.refresh(item)
        
        logger.warning(
            f"DLQ item created: id={item.id}, type={event_type.value}, "
            f"user={user_id[:50]}, amount={amount}, operation={operation_type}"
        )
        
        return item
    except Exception as e:
        await db.rollback()
        logger.error(f"CRITICAL: Failed to add DLQ item: {e}")
        raise


async def add_refund_failure_to_dlq(
    db: AsyncSession,
    user_id: str,
    amount: int,
    operation_type: str,
    error: Exception,
    context: Optional[dict] = None,
) -> DeadLetterQueueItem:
    """
    Convenience function to add a failed refund to DLQ.
    
    Args:
        db: Database session
        user_id: User who should have received the refund
        amount: Credit amount that should have been refunded
        operation_type: What capsule/operation failed
        error: The exception that occurred
        context: Additional context (capsule inputs, etc.)
    
    Returns:
        Created DLQ item
    """
    import traceback
    
    return await add_to_dlq(
        db=db,
        event_type=DLQEventType.REFUND_FAILED,
        user_id=user_id,
        operation_type=operation_type,
        error_message=str(error),
        amount=amount,
        error_type=type(error).__name__,
        stack_trace=traceback.format_exc(),
        original_payload={
            "refund_amount": amount,
            "capsule": operation_type,
            **(context or {}),
        },
    )


# =============================================================================
# DLQ Queries
# =============================================================================

async def list_dlq_items(
    db: AsyncSession,
    status: Optional[DLQStatus] = None,
    event_type: Optional[DLQEventType] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[DeadLetterQueueItem], int]:
    """
    List DLQ items with optional filters.
    
    Returns:
        Tuple of (items, total_count)
    """
    query = select(DeadLetterQueueItem)
    count_query = select(func.count(DeadLetterQueueItem.id))
    
    if status:
        query = query.where(DeadLetterQueueItem.status == status.value)
        count_query = count_query.where(DeadLetterQueueItem.status == status.value)
    
    if event_type:
        query = query.where(DeadLetterQueueItem.event_type == event_type.value)
        count_query = count_query.where(DeadLetterQueueItem.event_type == event_type.value)
    
    if user_id:
        query = query.where(DeadLetterQueueItem.user_id == user_id)
        count_query = count_query.where(DeadLetterQueueItem.user_id == user_id)
    
    query = query.order_by(DeadLetterQueueItem.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    return list(items), total


async def get_dlq_item(db: AsyncSession, item_id: UUID) -> Optional[DeadLetterQueueItem]:
    """Get a specific DLQ item by ID."""
    result = await db.execute(
        select(DeadLetterQueueItem).where(DeadLetterQueueItem.id == item_id)
    )
    return result.scalars().first()


async def get_dlq_stats(db: AsyncSession) -> dict:
    """Get DLQ statistics for dashboard."""
    # Count by status
    status_counts = {}
    for status in DLQStatus:
        result = await db.execute(
            select(func.count(DeadLetterQueueItem.id))
            .where(DeadLetterQueueItem.status == status.value)
        )
        status_counts[status.value] = result.scalar() or 0
    
    # Count by event type
    type_counts = {}
    for event_type in DLQEventType:
        result = await db.execute(
            select(func.count(DeadLetterQueueItem.id))
            .where(DeadLetterQueueItem.event_type == event_type.value)
            .where(DeadLetterQueueItem.status == DLQStatus.PENDING.value)
        )
        type_counts[event_type.value] = result.scalar() or 0
    
    # Total pending credits
    result = await db.execute(
        select(func.sum(DeadLetterQueueItem.amount))
        .where(DeadLetterQueueItem.status == DLQStatus.PENDING.value)
        .where(DeadLetterQueueItem.event_type == DLQEventType.REFUND_FAILED.value)
    )
    pending_refund_credits = result.scalar() or 0
    
    return {
        "by_status": status_counts,
        "pending_by_type": type_counts,
        "pending_refund_credits": pending_refund_credits,
        "total_pending": status_counts.get(DLQStatus.PENDING.value, 0),
    }


# =============================================================================
# DLQ Resolution
# =============================================================================

async def retry_dlq_item(
    db: AsyncSession,
    item_id: UUID,
    processed_by: str,
) -> Tuple[bool, Optional[str]]:
    """
    Retry processing a DLQ item (e.g., retry a failed refund).
    
    Args:
        db: Database session
        item_id: DLQ item ID
        processed_by: Admin user ID
    
    Returns:
        Tuple of (success, error_message)
    """
    item = await get_dlq_item(db, item_id)
    if not item:
        return False, "DLQ item not found"
    
    if item.status != DLQStatus.PENDING.value:
        return False, f"Item is not pending (status: {item.status})"
    
    if item.retry_count >= item.max_retries:
        return False, f"Max retries exceeded ({item.max_retries})"
    
    # Mark as processing
    item.status = DLQStatus.PROCESSING.value
    item.last_retry_at = datetime.utcnow()
    item.retry_count += 1
    await db.commit()
    
    try:
        # Handle based on event type
        if item.event_type == DLQEventType.REFUND_FAILED.value:
            success, error = await _retry_refund(db, item)
        elif item.event_type == DLQEventType.PAYOUT_FAILED.value:
            success, error = await _retry_payout(db, item)
        else:
            success, error = False, f"Unknown event type: {item.event_type}"
        
        if success:
            item.status = DLQStatus.RESOLVED.value
            item.resolved_by = processed_by
            item.resolved_at = datetime.utcnow()
            item.resolution_notes = "Auto-resolved via retry"
            logger.info(f"DLQ item resolved: id={item.id}")
        else:
            item.status = DLQStatus.PENDING.value  # Back to pending for manual review
            item.resolution_notes = f"Retry failed: {error}"
            logger.warning(f"DLQ retry failed: id={item.id}, error={error}")
        
        await db.commit()
        return success, error
        
    except Exception as e:
        item.status = DLQStatus.PENDING.value
        item.resolution_notes = f"Retry exception: {str(e)}"
        await db.commit()
        logger.exception(f"DLQ retry exception: id={item.id}")
        return False, str(e)


async def _retry_refund(
    db: AsyncSession,
    item: DeadLetterQueueItem,
) -> Tuple[bool, Optional[str]]:
    """Retry a failed refund."""
    from app.credit_service import refund_credits
    
    user_id = item.user_id
    amount = item.amount
    
    if not user_id or amount <= 0:
        return False, "Invalid user_id or amount"
    
    try:
        await refund_credits(
            db=db,
            user_id=user_id,
            amount=amount,
            description=f"DLQ Retry: {item.operation_type}",
            meta={"dlq_id": str(item.id), "original_error": item.error_type},
        )
        return True, None
    except Exception as e:
        return False, str(e)


async def _retry_payout(
    db: AsyncSession,
    item: DeadLetterQueueItem,
) -> Tuple[bool, Optional[str]]:
    """Retry a failed payout (settlement)."""
    from app.credit_service import grant_promo_credits
    
    payload = item.original_payload or {}
    recipient_id = payload.get("recipient_id")
    amount = item.amount
    
    if not recipient_id or amount <= 0:
        return False, "Invalid recipient_id or amount"
    
    try:
        await grant_promo_credits(
            db=db,
            user_id=recipient_id,
            amount=amount,
            reason=f"DLQ Payout Retry: {item.operation_type}",
            expires_in_days=365,
        )
        return True, None
    except Exception as e:
        return False, str(e)


async def resolve_dlq_item(
    db: AsyncSession,
    item_id: UUID,
    resolved_by: str,
    resolution_notes: str,
    skip: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Manually resolve a DLQ item.
    
    Args:
        db: Database session
        item_id: DLQ item ID
        resolved_by: Admin user ID
        resolution_notes: Notes explaining the resolution
        skip: If True, mark as skipped instead of resolved
    
    Returns:
        Tuple of (success, error_message)
    """
    item = await get_dlq_item(db, item_id)
    if not item:
        return False, "DLQ item not found"
    
    if item.status not in [DLQStatus.PENDING.value, DLQStatus.PROCESSING.value]:
        return False, f"Item is not pending/processing (status: {item.status})"
    
    item.status = DLQStatus.SKIPPED.value if skip else DLQStatus.RESOLVED.value
    item.resolved_by = resolved_by
    item.resolved_at = datetime.utcnow()
    item.resolution_notes = resolution_notes
    
    await db.commit()
    
    logger.info(
        f"DLQ item manually resolved: id={item.id}, "
        f"status={'skipped' if skip else 'resolved'}, by={resolved_by}"
    )
    
    return True, None
