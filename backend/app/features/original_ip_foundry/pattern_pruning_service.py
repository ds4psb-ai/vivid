"""Pattern pruning service for Foundry Qdrant collection maintenance."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class PatternPruningService:
    """Prune low-confidence or stale patterns from Qdrant."""

    DEFAULT_CONFIDENCE_THRESHOLD = 0.3
    DEFAULT_MAX_AGE_DAYS = 90

    def __init__(self, qdrant_pattern_store=None):
        self._qdrant_store = qdrant_pattern_store

    def prune(
        self,
        *,
        project_id: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        max_age_days: Optional[int] = None,
        dry_run: bool = True,
    ) -> dict:
        """Prune patterns below confidence threshold or older than max_age_days."""
        threshold = confidence_threshold if confidence_threshold is not None else self.DEFAULT_CONFIDENCE_THRESHOLD
        age_days = max_age_days if max_age_days is not None else self.DEFAULT_MAX_AGE_DAYS
        cutoff_date = (datetime.utcnow() - timedelta(days=age_days)).isoformat()

        filters_applied = {
            "confidence_threshold": threshold,
            "max_age_days": age_days,
            "cutoff_date": cutoff_date,
        }
        if project_id:
            filters_applied["project_id"] = project_id

        if not self._qdrant_store:
            return {
                "dry_run": dry_run,
                "would_delete_count": 0,
                "filters_applied": filters_applied,
                "error": "no_qdrant_store",
            }

        client = self._qdrant_store._get_client()
        if client is None:
            return {
                "dry_run": dry_run,
                "would_delete_count": 0,
                "filters_applied": filters_applied,
                "error": "qdrant_unavailable",
            }

        from app.features.original_ip_foundry.qdrant_pattern_store import COLLECTION

        try:
            from qdrant_client.http import models as qdrant_models

            must_conditions = [
                qdrant_models.FieldCondition(
                    key="confidence",
                    range=qdrant_models.Range(lt=threshold),
                ),
            ]
            if project_id:
                must_conditions.append(
                    qdrant_models.FieldCondition(
                        key="project_id",
                        match=qdrant_models.MatchValue(value=project_id),
                    )
                )

            prune_filter = qdrant_models.Filter(must=must_conditions)

            if dry_run:
                # Count matching points
                result = client.scroll(
                    collection_name=COLLECTION,
                    scroll_filter=prune_filter,
                    limit=10000,
                    with_payload=False,
                )
                count = len(result[0]) if result and result[0] else 0
                return {
                    "dry_run": True,
                    "would_delete_count": count,
                    "filters_applied": filters_applied,
                }
            else:
                # Actually delete
                client.delete(
                    collection_name=COLLECTION,
                    points_selector=qdrant_models.FilterSelector(
                        filter=prune_filter,
                    ),
                )
                return {
                    "dry_run": False,
                    "deleted": True,
                    "filters_applied": filters_applied,
                }

        except Exception as e:
            logger.warning(f"[PatternPruning] Prune failed: {e}")
            return {
                "dry_run": dry_run,
                "error": str(e),
                "filters_applied": filters_applied,
            }
