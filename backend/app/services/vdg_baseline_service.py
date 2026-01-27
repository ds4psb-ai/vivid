"""VDG Baseline Service for ML Drift Detection

Manages baseline storage and retrieval for VDG feature distributions.

Usage:
    from app.services.vdg_baseline_service import VDGBaselineService

    async with async_session_maker() as db:
        service = VDGBaselineService(db)
        await service.create_baseline("hook_score", values, period_days=7)
        baseline_df = await service.get_baseline_dataframe()
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import VDGDriftBaseline, OutlierItem
from app.services.vdg_feature_extractor import VDGFeatureExtractor, get_feature_extractor

logger = logging.getLogger(__name__)


class VDGBaselineService:
    """
    VDG Feature Baseline 관리 서비스

    Responsibilities:
    - Create baselines from historical data
    - Retrieve baseline distributions
    - Generate DataFrames for Evidently AI
    """

    MIN_SAMPLES = 30  # Minimum samples required for baseline

    def __init__(self, db: AsyncSession):
        self.db = db
        self.extractor = get_feature_extractor()

    async def create_baseline(
        self,
        feature_name: str,
        values: List[float],
        period_days: int = 7,
    ) -> Dict[str, Any]:
        """
        새 baseline 생성

        Args:
            feature_name: Feature name (e.g., "hook_score")
            values: List of feature values
            period_days: Period this baseline covers

        Returns:
            Created baseline info

        Raises:
            ValueError: If insufficient data
        """
        if len(values) < self.MIN_SAMPLES:
            raise ValueError(f"Insufficient data for {feature_name}: " f"{len(values)} < {self.MIN_SAMPLES} minimum")

        # Calculate histogram distribution
        hist, bin_edges = np.histogram(values, bins=10)
        distribution = {
            "bins": bin_edges.tolist(),
            "counts": hist.tolist(),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "percentiles": {
                "p25": float(np.percentile(values, 25)),
                "p50": float(np.percentile(values, 50)),
                "p75": float(np.percentile(values, 75)),
                "p95": float(np.percentile(values, 95)),
            },
        }

        # Deactivate old baselines for this feature
        await self._deactivate_old_baselines(feature_name)

        # Create new baseline
        now = datetime.utcnow()
        baseline = VDGDriftBaseline(
            feature_name=feature_name,
            baseline_distribution=distribution,
            sample_count=len(values),
            period_start=now - timedelta(days=period_days),
            period_end=now,
            is_active=True,
            extra_metadata={"method": "histogram", "bins": 10},
        )

        self.db.add(baseline)
        await self.db.commit()
        await self.db.refresh(baseline)

        logger.info(
            f"[BaselineService] Created baseline for {feature_name}: "
            f"{len(values)} samples, mean={distribution['mean']:.4f}"
        )

        return {
            "id": str(baseline.id),
            "feature_name": feature_name,
            "sample_count": len(values),
            "distribution": distribution,
        }

    async def create_all_baselines(
        self,
        period_days: int = 7,
    ) -> Dict[str, Any]:
        """
        모든 tracked features에 대한 baseline 생성

        Args:
            period_days: Period to use for baseline data

        Returns:
            Summary of created baselines
        """
        # Get completed items from the period
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        stmt = select(OutlierItem).where(
            and_(
                OutlierItem.analysis_status == "completed",
                OutlierItem.vdg_feature_vector.isnot(None),
                OutlierItem.updated_at >= cutoff,
            )
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        if len(items) < self.MIN_SAMPLES:
            logger.warning(f"[BaselineService] Insufficient items for baseline: " f"{len(items)} < {self.MIN_SAMPLES}")
            return {"error": "insufficient_data", "count": len(items)}

        # Extract feature values
        feature_values: Dict[str, List[float]] = {feat: [] for feat in self.extractor.TRACKED_FEATURES}

        for item in items:
            features = item.vdg_feature_vector
            if features:
                for feat_name in self.extractor.TRACKED_FEATURES:
                    if feat_name in features:
                        feature_values[feat_name].append(features[feat_name])

        # Create baseline for each feature
        created = []
        for feat_name, values in feature_values.items():
            if len(values) >= self.MIN_SAMPLES:
                try:
                    result = await self.create_baseline(feat_name, values, period_days)
                    created.append(result)
                except Exception as e:
                    logger.error(f"[BaselineService] Failed to create baseline " f"for {feat_name}: {e}")

        return {
            "created_count": len(created),
            "baselines": created,
            "total_items": len(items),
        }

    async def get_active_baseline(self, feature_name: str) -> Optional[VDGDriftBaseline]:
        """
        특정 feature의 활성 baseline 조회

        Args:
            feature_name: Feature name

        Returns:
            Active baseline or None
        """
        stmt = (
            select(VDGDriftBaseline)
            .where(
                and_(
                    VDGDriftBaseline.feature_name == feature_name,
                    VDGDriftBaseline.is_active == True,  # noqa: E712
                )
            )
            .order_by(VDGDriftBaseline.created_at.desc())
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active_baselines(self) -> List[VDGDriftBaseline]:
        """
        모든 활성 baselines 조회

        Returns:
            List of active baselines
        """
        stmt = (
            select(VDGDriftBaseline)
            .where(
                VDGDriftBaseline.is_active == True  # noqa: E712
            )
            .order_by(VDGDriftBaseline.feature_name)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_baseline_dataframe(self) -> Optional[Any]:
        """
        Baseline 데이터를 Evidently AI용 DataFrame으로 변환

        Note: Returns pandas DataFrame if available, otherwise dict

        Returns:
            DataFrame with baseline feature values, or None if no data
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("[BaselineService] pandas not installed")
            return None

        baselines = await self.get_all_active_baselines()
        if not baselines:
            logger.warning("[BaselineService] No active baselines found")
            return None

        # Reconstruct samples from distribution (approximation)
        # This generates synthetic samples matching the distribution
        data: Dict[str, List[float]] = {}

        for baseline in baselines:
            dist = baseline.baseline_distribution
            feature = baseline.feature_name

            # Generate samples from histogram
            bins = dist.get("bins", [])
            counts = dist.get("counts", [])

            if len(bins) > 1 and len(counts) > 0:
                samples = []
                for i, count in enumerate(counts):
                    if count > 0:
                        # Generate values uniformly in each bin
                        bin_min = bins[i]
                        bin_max = bins[i + 1]
                        bin_samples = np.random.uniform(bin_min, bin_max, size=count).tolist()
                        samples.extend(bin_samples)
                data[feature] = samples

        if not data:
            return None

        # Ensure all features have same length (pad with mean)
        max_len = max(len(v) for v in data.values())
        for feature, values in data.items():
            if len(values) < max_len:
                mean_val = np.mean(values)
                data[feature].extend([mean_val] * (max_len - len(values)))

        return pd.DataFrame(data)

    async def get_recent_dataframe(self, days: int = 7) -> Optional[Any]:
        """
        최근 N일간의 VDG 분석 결과를 DataFrame으로 변환

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with recent feature values, or None if insufficient data
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("[BaselineService] pandas not installed")
            return None

        cutoff = datetime.utcnow() - timedelta(days=days)

        stmt = select(OutlierItem).where(
            and_(
                OutlierItem.analysis_status == "completed",
                OutlierItem.vdg_feature_vector.isnot(None),
                OutlierItem.updated_at >= cutoff,
            )
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        if len(items) < self.MIN_SAMPLES:
            logger.warning(f"[BaselineService] Insufficient recent items: " f"{len(items)} < {self.MIN_SAMPLES}")
            return None

        # Extract features
        data: Dict[str, List[float]] = {feat: [] for feat in self.extractor.TRACKED_FEATURES}

        for item in items:
            features = item.vdg_feature_vector
            if features:
                for feat_name in self.extractor.TRACKED_FEATURES:
                    if feat_name in features:
                        data[feat_name].append(features[feat_name])

        # Filter features with enough data
        valid_data = {k: v for k, v in data.items() if len(v) >= self.MIN_SAMPLES}

        if not valid_data:
            return None

        # Ensure same length
        min_len = min(len(v) for v in valid_data.values())
        for feature in valid_data:
            valid_data[feature] = valid_data[feature][:min_len]

        return pd.DataFrame(valid_data)

    async def _deactivate_old_baselines(self, feature_name: str) -> int:
        """
        특정 feature의 기존 baselines 비활성화

        Args:
            feature_name: Feature name

        Returns:
            Number of deactivated baselines
        """
        stmt = (
            update(VDGDriftBaseline)
            .where(
                and_(
                    VDGDriftBaseline.feature_name == feature_name,
                    VDGDriftBaseline.is_active == True,  # noqa: E712
                )
            )
            .values(is_active=False)
        )

        result = await self.db.execute(stmt)
        count = result.rowcount
        await self.db.commit()

        if count > 0:
            logger.info(f"[BaselineService] Deactivated {count} old baselines " f"for {feature_name}")

        return count

    async def get_baseline_stats(self) -> Dict[str, Any]:
        """
        Baseline 상태 요약 조회

        Returns:
            Summary statistics
        """
        baselines = await self.get_all_active_baselines()

        if not baselines:
            return {"status": "no_baselines", "features": []}

        features_info = []
        for baseline in baselines:
            dist = baseline.baseline_distribution
            features_info.append(
                {
                    "feature_name": baseline.feature_name,
                    "sample_count": baseline.sample_count,
                    "mean": dist.get("mean"),
                    "std": dist.get("std"),
                    "period_start": baseline.period_start.isoformat(),
                    "period_end": baseline.period_end.isoformat(),
                }
            )

        return {
            "status": "active",
            "feature_count": len(baselines),
            "features": features_info,
        }
