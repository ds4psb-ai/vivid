"""Logic Vector Versioning Service.

Manages Logic Vector versions per IP with drift detection.
Implements 2026 MLOps best practices for model versioning:
- Kolmogorov-Smirnov test for distribution shift
- Cosine similarity for embedding drift
- Automatic version management with validity periods

Usage:
    from app.services.logic_vector_versioning import LogicVectorVersioning

    versioning = LogicVectorVersioning()

    # Detect drift from new videos
    result = await versioning.detect_drift(
        ip_id="my-ip",
        new_videos=["gs://bucket/new1.mp4", "gs://bucket/new2.mp4"],
        db=db,
    )

    # Create new version if drift detected
    if result.action == DriftAction.REQUIRE_HUMAN_REVIEW:
        # Queue for HITL review
        await versioning.queue_for_review(ip_id, result, new_vector, db)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import stats
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.drift_detection import (
    DriftAction,
    DriftDetectionResult,
    DriftMetrics,
    DriftReason,
    LogicVectorVersionCreate,
)
from app.schemas.vpe import CameraGrammar, LogicVector

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Drift thresholds (2026 best practices)
DRIFT_THRESHOLD = 0.15  # Cosine distance > 15% = significant drift
KS_PVALUE_THRESHOLD = 0.05  # p-value < 0.05 = significant distribution shift
CADENCE_DRIFT_THRESHOLD = 0.20  # 20% change in cadence patterns

# Auto-upgrade threshold (safe to auto-apply)
AUTO_UPGRADE_THRESHOLD = 0.05  # Very small drift, likely noise


# =============================================================================
# Logic Vector Versioning Service
# =============================================================================

class LogicVectorVersioning:
    """Logic Vector v1 → v2 → v3 evolution management.

    Detects style drift and manages version transitions.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize versioning service.

        Args:
            api_key: Optional API key for VPE analysis
        """
        self._api_key = api_key or settings.GEMINI_API_KEY.get_secret_value()

    async def detect_drift(
        self,
        ip_id: str,
        new_videos: List[str],
        db: AsyncSession,
    ) -> DriftDetectionResult:
        """Detect style drift from new videos.

        Args:
            ip_id: IP identifier
            new_videos: List of new video URIs to analyze
            db: Database session

        Returns:
            DriftDetectionResult with action recommendation
        """
        # Get current active version
        current = await self._get_active_version(ip_id, db)

        if current is None:
            # No existing version - this is the first
            return DriftDetectionResult(
                action=DriftAction.AUTO_UPGRADE,
                proposed_version=1,
                drift_score=0.0,
                reason=DriftReason.MANUAL_UPDATE,
                confidence=1.0,
                details="No existing version found. Creating initial version.",
            )

        # Extract aggregate Logic Vector from new videos
        new_vector = await self._extract_aggregate_vector(new_videos)

        if new_vector is None:
            return DriftDetectionResult(
                action=DriftAction.NO_CHANGE,
                current_version=current["version_number"],
                drift_score=0.0,
                confidence=0.3,
                details="Failed to extract Logic Vector from new videos.",
            )

        # Calculate drift metrics
        metrics = self._calculate_drift_metrics(
            current["logic_vector"],
            new_vector.model_dump(),
            current.get("embedding"),
        )

        # Determine action based on drift score
        drift_score = metrics.cosine_distance
        action = self._determine_action(drift_score, metrics)
        reason = self._infer_drift_reason(metrics, current["logic_vector"], new_vector.model_dump())

        return DriftDetectionResult(
            action=action,
            current_version=current["version_number"],
            proposed_version=current["version_number"] + 1,
            drift_score=drift_score,
            metrics=metrics,
            reason=reason,
            confidence=self._calculate_confidence(metrics),
            details=self._generate_details(metrics, reason),
        )

    async def create_version(
        self,
        request: LogicVectorVersionCreate,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Create a new Logic Vector version.

        Args:
            request: Version creation request
            db: Database session

        Returns:
            Created version record
        """
        from app.models_logic_vector import LogicVectorVersion

        # Get next version number
        current = await self._get_active_version(request.ip_id, db)
        next_version = (current["version_number"] + 1) if current else 1

        # Deactivate current version
        if current:
            await db.execute(
                update(LogicVectorVersion)
                .where(LogicVectorVersion.ip_id == request.ip_id)
                .where(LogicVectorVersion.is_active == True)
                .values(is_active=False, valid_until=datetime.utcnow())
            )

        # Create new version
        new_version = LogicVectorVersion(
            id=uuid.uuid4(),
            ip_id=request.ip_id,
            version_number=next_version,
            embedding=request.embedding,
            logic_vector=request.logic_vector,
            source_videos=request.source_videos,
            is_active=True,
            valid_from=datetime.utcnow(),
            drift_score_from_prev=request.drift_score_from_prev,
            drift_reason=request.drift_reason.value if request.drift_reason else None,
            created_by=request.created_by,
        )

        db.add(new_version)
        await db.flush()

        logger.info(
            f"[Versioning] Created version {next_version} for IP {request.ip_id}, "
            f"drift_score={request.drift_score_from_prev}"
        )

        return {
            "id": str(new_version.id),
            "ip_id": new_version.ip_id,
            "version_number": new_version.version_number,
            "is_active": new_version.is_active,
            "created_at": new_version.created_at.isoformat(),
        }

    async def get_version_history(
        self,
        ip_id: str,
        db: AsyncSession,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get version history for an IP.

        Args:
            ip_id: IP identifier
            db: Database session
            limit: Maximum versions to return

        Returns:
            List of version records
        """
        from app.models_logic_vector import LogicVectorVersion

        query = (
            select(LogicVectorVersion)
            .where(LogicVectorVersion.ip_id == ip_id)
            .order_by(LogicVectorVersion.version_number.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        versions = result.scalars().all()

        return [
            {
                "id": str(v.id),
                "ip_id": v.ip_id,
                "version_number": v.version_number,
                "is_active": v.is_active,
                "valid_from": v.valid_from.isoformat() if v.valid_from else None,
                "valid_until": v.valid_until.isoformat() if v.valid_until else None,
                "drift_score_from_prev": v.drift_score_from_prev,
                "drift_reason": v.drift_reason,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ]

    async def queue_for_review(
        self,
        ip_id: str,
        drift_result: DriftDetectionResult,
        new_vector: LogicVector,
        source_videos: List[str],
        db: AsyncSession,
    ) -> str:
        """Queue drift detection for HITL review.

        Args:
            ip_id: IP identifier
            drift_result: Drift detection result
            new_vector: Proposed new Logic Vector
            source_videos: Source videos for the new vector
            db: Database session

        Returns:
            HITL review item ID
        """
        from app.services.hitl_workflow import HITLWorkflowService

        hitl_service = HITLWorkflowService()

        payload = {
            "ip_id": ip_id,
            "current_version": drift_result.current_version,
            "proposed_version": drift_result.proposed_version,
            "drift_score": drift_result.drift_score,
            "drift_reason": drift_result.reason.value if drift_result.reason else None,
            "new_logic_vector": new_vector.model_dump(),
            "source_videos": source_videos,
            "details": drift_result.details,
        }

        suggested_action = {
            "action": "create_version",
            "ip_id": ip_id,
            "logic_vector": new_vector.model_dump(),
            "source_videos": source_videos,
            "drift_reason": drift_result.reason.value if drift_result.reason else None,
        }

        item = await hitl_service.create_review_item(
            review_type="vector_drift",
            payload=payload,
            severity="high" if drift_result.drift_score > 0.3 else "medium",
            suggested_action=suggested_action,
            db=db,
        )

        return str(item.id)

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_active_version(
        self,
        ip_id: str,
        db: AsyncSession,
    ) -> Optional[Dict[str, Any]]:
        """Get the current active version for an IP."""
        try:
            from app.models_logic_vector import LogicVectorVersion

            query = (
                select(LogicVectorVersion)
                .where(LogicVectorVersion.ip_id == ip_id)
                .where(LogicVectorVersion.is_active == True)
            )

            result = await db.execute(query)
            version = result.scalar_one_or_none()

            if version:
                return {
                    "id": str(version.id),
                    "ip_id": version.ip_id,
                    "version_number": version.version_number,
                    "logic_vector": version.logic_vector,
                    "embedding": version.embedding,
                    "source_videos": version.source_videos,
                }

        except ImportError:
            logger.warning("[Versioning] LogicVectorVersion model not found")
        except Exception as e:
            logger.error(f"[Versioning] Failed to get active version: {e}")

        return None

    async def _extract_aggregate_vector(
        self,
        video_uris: List[str],
    ) -> Optional[LogicVector]:
        """Extract and aggregate Logic Vector from multiple videos."""
        from app.services.vpe_service import get_vpe_service

        if not video_uris:
            return None

        vpe_service = get_vpe_service(api_key=self._api_key)

        vectors = []
        for uri in video_uris[:5]:  # Limit to 5 videos
            try:
                result = await vpe_service.parse_video(
                    video_uri=uri,
                    extract_shots=False,
                )
                if result.success and result.logic_vector:
                    vectors.append(result.logic_vector)
            except Exception as e:
                logger.warning(f"[Versioning] Failed to parse {uri}: {e}")

        if not vectors:
            return None

        # Aggregate vectors (average numerical values)
        return self._average_logic_vectors(vectors)

    def _average_logic_vectors(self, vectors: List[LogicVector]) -> LogicVector:
        """Average multiple Logic Vectors into one."""
        if len(vectors) == 1:
            return vectors[0]

        # Average camera grammar ratios
        avg_camera = CameraGrammar(
            static=np.mean([v.camera_grammar.static for v in vectors]),
            dolly=np.mean([v.camera_grammar.dolly for v in vectors]),
            handheld=np.mean([v.camera_grammar.handheld for v in vectors]),
            push_in=np.mean([v.camera_grammar.push_in for v in vectors]),
            pull_out=np.mean([v.camera_grammar.pull_out for v in vectors]),
            pan=np.mean([v.camera_grammar.pan for v in vectors]),
            tilt=np.mean([v.camera_grammar.tilt for v in vectors]),
            crane=np.mean([v.camera_grammar.crane for v in vectors]),
            tracking=np.mean([v.camera_grammar.tracking for v in vectors]),
            steadicam=np.mean([v.camera_grammar.steadicam for v in vectors]),
        )

        # Take first vector as base and update with averages
        base = vectors[0].model_copy()
        base.camera_grammar = avg_camera
        base.composition.symmetry_score = np.mean([v.composition.symmetry_score for v in vectors])
        base.confidence = np.mean([v.confidence for v in vectors])

        return base

    def _calculate_drift_metrics(
        self,
        old_vector: Dict[str, Any],
        new_vector: Dict[str, Any],
        old_embedding: Optional[List[float]],
    ) -> DriftMetrics:
        """Calculate drift metrics between two Logic Vectors."""
        # Camera grammar KS test
        old_camera = old_vector.get("camera_grammar", {})
        new_camera = new_vector.get("camera_grammar", {})

        old_dist = [
            old_camera.get("static", 0),
            old_camera.get("dolly", 0),
            old_camera.get("handheld", 0),
            old_camera.get("pan", 0),
            old_camera.get("tilt", 0),
        ]
        new_dist = [
            new_camera.get("static", 0),
            new_camera.get("dolly", 0),
            new_camera.get("handheld", 0),
            new_camera.get("pan", 0),
            new_camera.get("tilt", 0),
        ]

        # KS test for camera grammar distribution
        try:
            ks_result = stats.ks_2samp(old_dist, new_dist)
            ks_statistic = float(ks_result.statistic)
            ks_pvalue = float(ks_result.pvalue)
        except Exception:
            ks_statistic = None
            ks_pvalue = None

        # Cosine distance (simplified - using camera grammar as proxy)
        old_vec = np.array(old_dist)
        new_vec = np.array(new_dist)

        norm_old = np.linalg.norm(old_vec)
        norm_new = np.linalg.norm(new_vec)

        if norm_old > 0 and norm_new > 0:
            cosine_sim = np.dot(old_vec, new_vec) / (norm_old * norm_new)
            cosine_distance = 1 - cosine_sim
        else:
            cosine_distance = 1.0

        # Camera grammar drift
        camera_drift = np.mean(np.abs(np.array(old_dist) - np.array(new_dist)))

        # Cadence drift
        old_cadence = old_vector.get("cadence", {})
        new_cadence = new_vector.get("cadence", {})
        cadence_drift = self._calculate_cadence_drift(old_cadence, new_cadence)

        return DriftMetrics(
            cosine_distance=float(max(0, min(2, cosine_distance))),
            ks_statistic=ks_statistic,
            ks_pvalue=ks_pvalue,
            cadence_drift=cadence_drift,
            camera_grammar_drift=float(camera_drift),
        )

    def _calculate_cadence_drift(
        self,
        old_cadence: Dict[str, Any],
        new_cadence: Dict[str, Any],
    ) -> float:
        """Calculate drift in cadence patterns."""
        old_hook = old_cadence.get("hook", 0)
        new_hook = new_cadence.get("hook", 0)

        old_build = old_cadence.get("build", 0)
        new_build = new_cadence.get("build", 0)

        old_climax = old_cadence.get("climax", 0)
        new_climax = new_cadence.get("climax", 0)

        # Calculate relative change in timing ratios
        diffs = []

        if old_hook > 0:
            diffs.append(abs(new_hook - old_hook) / old_hook)
        if old_build > 0:
            diffs.append(abs(new_build - old_build) / old_build)
        if old_climax > 0:
            diffs.append(abs(new_climax - old_climax) / old_climax)

        return float(np.mean(diffs)) if diffs else 0.0

    def _determine_action(
        self,
        drift_score: float,
        metrics: DriftMetrics,
    ) -> DriftAction:
        """Determine recommended action based on drift metrics."""
        # Very small drift - likely noise
        if drift_score < AUTO_UPGRADE_THRESHOLD:
            return DriftAction.NO_CHANGE

        # Significant drift - needs review
        if drift_score > DRIFT_THRESHOLD:
            return DriftAction.REQUIRE_HUMAN_REVIEW

        # KS test indicates significant distribution shift
        if metrics.ks_pvalue and metrics.ks_pvalue < KS_PVALUE_THRESHOLD:
            return DriftAction.REQUIRE_HUMAN_REVIEW

        # Moderate drift - could auto-upgrade with caution
        if drift_score > AUTO_UPGRADE_THRESHOLD:
            return DriftAction.AUTO_UPGRADE

        return DriftAction.NO_CHANGE

    def _infer_drift_reason(
        self,
        metrics: DriftMetrics,
        old_vector: Dict[str, Any],
        new_vector: Dict[str, Any],
    ) -> Optional[DriftReason]:
        """Infer the reason for drift based on metrics."""
        # High cadence drift suggests platform shift (different content lengths)
        if metrics.cadence_drift and metrics.cadence_drift > CADENCE_DRIFT_THRESHOLD:
            return DriftReason.PLATFORM_SHIFT

        # Significant camera grammar change suggests style evolution
        if metrics.camera_grammar_drift and metrics.camera_grammar_drift > 0.2:
            return DriftReason.STYLE_EVOLUTION

        # General drift
        if metrics.cosine_distance > DRIFT_THRESHOLD:
            return DriftReason.CONTENT_EXPANSION

        return None

    def _calculate_confidence(self, metrics: DriftMetrics) -> float:
        """Calculate confidence in the drift assessment."""
        confidence = 0.5

        # Higher confidence if KS test is significant
        if metrics.ks_pvalue is not None:
            if metrics.ks_pvalue < 0.01:
                confidence += 0.3
            elif metrics.ks_pvalue < 0.05:
                confidence += 0.2

        # Higher confidence with more extreme drift scores
        if metrics.cosine_distance > 0.3:
            confidence += 0.2
        elif metrics.cosine_distance < 0.05:
            confidence += 0.1

        return min(1.0, confidence)

    def _generate_details(
        self,
        metrics: DriftMetrics,
        reason: Optional[DriftReason],
    ) -> str:
        """Generate human-readable drift details."""
        parts = []

        parts.append(f"Cosine distance: {metrics.cosine_distance:.3f}")

        if metrics.ks_statistic is not None:
            parts.append(f"KS statistic: {metrics.ks_statistic:.3f} (p={metrics.ks_pvalue:.3f})")

        if metrics.camera_grammar_drift is not None:
            parts.append(f"Camera grammar drift: {metrics.camera_grammar_drift:.3f}")

        if metrics.cadence_drift is not None:
            parts.append(f"Cadence drift: {metrics.cadence_drift:.3f}")

        if reason:
            parts.append(f"Inferred reason: {reason.value}")

        return " | ".join(parts)


# =============================================================================
# Module-level convenience
# =============================================================================

_default_service: Optional[LogicVectorVersioning] = None


def get_versioning_service(api_key: Optional[str] = None) -> LogicVectorVersioning:
    """Get or create the default versioning service."""
    global _default_service
    if api_key:
        return LogicVectorVersioning(api_key=api_key)
    if _default_service is None:
        _default_service = LogicVectorVersioning()
    return _default_service


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "LogicVectorVersioning",
    "DRIFT_THRESHOLD",
    "KS_PVALUE_THRESHOLD",
    "get_versioning_service",
]
