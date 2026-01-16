"""
A/B Testing Module - Self-Hosted Experimentation Infrastructure (2026 Best Practice)

Zero-cost experimentation platform with:
- Consistent user assignment (no flip-flopping)
- Statistical significance calculation (frequentist + Bayesian)
- Integration with Thompson Sampling (UQSL)
- CUPED variance reduction
"""

from app.experiments.ab_testing import (
    ABTestingService,
    get_ab_testing,
    init_ab_testing,
    ExperimentAssignment,
)
from app.experiments.statistics import (
    StatisticalAnalyzer,
    SignificanceResult,
    VariantStats,
    get_statistical_analyzer,
)
from app.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentExposure,
    ExperimentConversion,
    ExperimentResult,
    ExperimentStatus,
)

__all__ = [
    # Service
    "ABTestingService",
    "get_ab_testing",
    "init_ab_testing",
    "ExperimentAssignment",
    # Statistics
    "StatisticalAnalyzer",
    "SignificanceResult",
    "VariantStats",
    "get_statistical_analyzer",
    # Models
    "Experiment",
    "ExperimentVariant",
    "ExperimentExposure",
    "ExperimentConversion",
    "ExperimentResult",
    "ExperimentStatus",
]
