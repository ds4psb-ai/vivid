"""Outbox Publisher Service.

Polls the Outbox table and publishes events to external systems (Qdrant).
Implements reliable at-least-once delivery with exponential backoff.

Usage:
    from app.services.outbox_publisher import OutboxPublisher

    publisher = OutboxPublisher()

    # One-time publish
    await publisher.poll_and_publish(db)

    # Or run as background task
    await publisher.start_background_task()
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models_outbox import Outbox, OutboxStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_BATCH_SIZE = 100
DEFAULT_POLL_INTERVAL_SECONDS = 5
MAX_BACKOFF_SECONDS = 300  # 5 minutes


# =============================================================================
# Outbox Publisher
# =============================================================================

class OutboxPublisher:
    """Publisher for Transactional Outbox pattern.

    Polls the outbox table and publishes events to Qdrant.
    Handles retries with exponential backoff.
    """

    def __init__(
        self,
        batch_size: int = DEFAULT_BATCH_SIZE,
        poll_interval: int = DEFAULT_POLL_INTERVAL_SECONDS,
    ):
        """Initialize publisher.

        Args:
            batch_size: Max events to process per poll
            poll_interval: Seconds between polls
        """
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def poll_and_publish(self, db: AsyncSession) -> int:
        """Poll pending events and publish them.

        Args:
            db: Database session

        Returns:
            Number of successfully published events
        """
        published_count = 0

        try:
            # Fetch pending events
            pending = await self._get_pending_events(db)

            if not pending:
                return 0

            logger.info(f"[Outbox] Processing {len(pending)} pending events")

            for event in pending:
                try:
                    await self._publish_event(event, db)
                    event.mark_published()
                    published_count += 1
                    logger.debug(f"[Outbox] Published event {event.id}")

                except Exception as e:
                    error_msg = str(e)[:1000]
                    event.mark_failed(error_msg)
                    logger.warning(
                        f"[Outbox] Failed to publish {event.id}: {e}, "
                        f"retry {event.retry_count}/{event.max_retries}"
                    )

                    # Schedule next retry with backoff
                    if event.should_retry():
                        backoff = min(
                            2 ** event.retry_count * 10,
                            MAX_BACKOFF_SECONDS,
                        )
                        event.scheduled_at = datetime.utcnow() + timedelta(seconds=backoff)

            await db.commit()

            logger.info(f"[Outbox] Published {published_count}/{len(pending)} events")

        except Exception as e:
            logger.exception(f"[Outbox] Poll error: {e}")
            await db.rollback()

        return published_count

    async def _get_pending_events(self, db: AsyncSession) -> List[Outbox]:
        """Get pending events ready for publishing."""
        now = datetime.utcnow()

        query = (
            select(Outbox)
            .where(Outbox.status == OutboxStatus.PENDING.value)
            .where(
                (Outbox.scheduled_at == None) |
                (Outbox.scheduled_at <= now)
            )
            .order_by(Outbox.created_at.asc())
            .limit(self.batch_size)
            .with_for_update(skip_locked=True)  # Prevent concurrent processing
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _publish_event(self, event: Outbox, db: AsyncSession) -> None:
        """Publish a single event to the appropriate destination."""
        event_type = event.event_type
        payload = event.payload

        if event_type == "dna_lab_result":
            await self._publish_dna_lab_result(payload)
        elif event_type == "logic_vector_update":
            await self._publish_logic_vector_update(payload)
        elif event_type == "vector_drift":
            await self._publish_vector_drift(payload)
        else:
            logger.warning(f"[Outbox] Unknown event type: {event_type}")

    async def _publish_dna_lab_result(self, payload: Dict[str, Any]) -> None:
        """Publish DNA Lab result to Qdrant."""
        try:
            from app.rag.tier1_dimension_rag import get_tier1_rag

            rag = get_tier1_rag()

            # Store VPE Logic Vector
            if payload.get("vpe"):
                await rag.upsert_logic_vector(
                    trace_id=payload["trace_id"],
                    logic_vector=payload["vpe"],
                    metadata={
                        "user_id": payload.get("user_id"),
                        "ad": payload.get("ad"),
                        "mirror": payload.get("mirror"),
                    },
                )
                logger.debug(f"[Outbox] Stored VPE to Qdrant: {payload['trace_id']}")

        except ImportError:
            logger.warning("[Outbox] tier1_dimension_rag not available")
        except Exception as e:
            logger.error(f"[Outbox] Qdrant publish failed: {e}")
            raise

    async def _publish_logic_vector_update(self, payload: Dict[str, Any]) -> None:
        """Publish Logic Vector version update to Qdrant."""
        try:
            from app.rag.tier1_dimension_rag import get_tier1_rag

            rag = get_tier1_rag()
            await rag.update_logic_vector_version(
                ip_id=payload["ip_id"],
                version=payload["version"],
                logic_vector=payload["logic_vector"],
            )

        except ImportError:
            logger.warning("[Outbox] tier1_dimension_rag not available")
        except Exception as e:
            logger.error(f"[Outbox] Logic vector update failed: {e}")
            raise

    async def _publish_vector_drift(self, payload: Dict[str, Any]) -> None:
        """Publish vector drift event for monitoring."""
        try:
            from app.services.telemetry_integration import record_drift_event

            await record_drift_event(
                ip_id=payload["ip_id"],
                drift_score=payload["drift_score"],
                action=payload["action"],
            )

        except ImportError:
            logger.warning("[Outbox] telemetry_integration not available")
        except Exception as e:
            logger.error(f"[Outbox] Drift event publish failed: {e}")
            raise

    # =========================================================================
    # Background Task
    # =========================================================================

    async def start_background_task(self) -> None:
        """Start the background polling task."""
        if self._running:
            logger.warning("[Outbox] Background task already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("[Outbox] Background task started")

    async def stop_background_task(self) -> None:
        """Stop the background polling task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("[Outbox] Background task stopped")

    async def _poll_loop(self) -> None:
        """Background polling loop."""
        from app.database import get_db_context

        while self._running:
            try:
                async with get_db_context() as db:
                    await self.poll_and_publish(db)

            except Exception as e:
                logger.exception(f"[Outbox] Poll loop error: {e}")

            await asyncio.sleep(self.poll_interval)


# =============================================================================
# Module-level convenience
# =============================================================================

_default_publisher: Optional[OutboxPublisher] = None


def get_outbox_publisher() -> OutboxPublisher:
    """Get or create the default publisher instance."""
    global _default_publisher
    if _default_publisher is None:
        _default_publisher = OutboxPublisher()
    return _default_publisher


# =============================================================================
# CLI Entry Point
# =============================================================================

async def main():
    """CLI entry point for running the publisher."""
    import argparse

    parser = argparse.ArgumentParser(description="Outbox Publisher")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Batch size",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Poll interval in seconds",
    )
    args = parser.parse_args()

    publisher = OutboxPublisher(
        batch_size=args.batch_size,
        poll_interval=args.interval,
    )

    if args.once:
        from app.database import get_db_context
        async with get_db_context() as db:
            count = await publisher.poll_and_publish(db)
            print(f"Published {count} events")
    else:
        await publisher.start_background_task()
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            await publisher.stop_background_task()


if __name__ == "__main__":
    asyncio.run(main())


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "OutboxPublisher",
    "get_outbox_publisher",
]
