"""
Feature Flags Module - Self-Hosted Feature Management (2026 Best Practice)

Zero-cost, Redis-backed feature flag system with:
- Two-level caching (Local LRU + Redis)
- User targeting with context properties
- Percentage rollouts with consistent hashing
- Kill switches for emergency disable
- OpenFeature-inspired vendor-neutral API
"""

from app.features.flags import (
    FeatureFlagService,
    get_feature_flags,
    init_feature_flags,
    CachedFlag,
)
from app.features.models import FeatureFlag, FeatureFlagAudit, FlagStatus
from app.features.schemas import (
    FeatureContext,
    FeatureFlagCreate,
    FeatureFlagUpdate,
    FeatureFlagResponse,
    FeatureFlagEvaluation,
    StrategyConfig,
    VariantConfig,
    BulkEvaluationRequest,
    BulkEvaluationResponse,
)

__all__ = [
    # Service
    "FeatureFlagService",
    "get_feature_flags",
    "init_feature_flags",
    "CachedFlag",
    # Models
    "FeatureFlag",
    "FeatureFlagAudit",
    "FlagStatus",
    # Schemas
    "FeatureContext",
    "FeatureFlagCreate",
    "FeatureFlagUpdate",
    "FeatureFlagResponse",
    "FeatureFlagEvaluation",
    "StrategyConfig",
    "VariantConfig",
    "BulkEvaluationRequest",
    "BulkEvaluationResponse",
]
