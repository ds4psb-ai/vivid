"""
A/B Testing Pydantic Schemas (2026 Best Practice)

Pydantic v2 with ConfigDict pattern.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Experiment Schemas
# =============================================================================

class VariantConfig(BaseModel):
    """Variant configuration for experiment."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    weight: float = Field(..., ge=0, le=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    is_control: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "treatment_a",
                "weight": 50,
                "payload": {"button_color": "blue"},
                "is_control": False,
            }
        }
    )


class ExperimentCreate(BaseModel):
    """Create a new experiment."""
    experiment_key: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis: Optional[str] = None

    # Metrics
    primary_metric: str = Field(..., min_length=1)
    secondary_metrics: list[str] = Field(default_factory=list)

    # Variants
    variants: list[VariantConfig] = Field(..., min_length=2)

    # Traffic allocation
    traffic_percentage: float = Field(default=100.0, ge=0, le=100)

    # Statistical settings
    min_sample_size: int = Field(default=1000, ge=100)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)
    min_detectable_effect: float = Field(default=0.05, ge=0.01, le=0.5)

    # Metadata
    owner: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    feature_flag_key: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_key": "checkout_flow_v2",
                "name": "Checkout Flow V2 Test",
                "hypothesis": "New checkout will increase conversion by 5%",
                "primary_metric": "purchase_completed",
                "variants": [
                    {"name": "control", "weight": 50, "is_control": True},
                    {"name": "treatment", "weight": 50, "is_control": False},
                ],
                "traffic_percentage": 10,
            }
        }
    )


class ExperimentUpdate(BaseModel):
    """Update experiment settings."""
    name: Optional[str] = None
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    traffic_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    secondary_metrics: Optional[list[str]] = None
    owner: Optional[str] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(extra="forbid")


class ExperimentResponse(BaseModel):
    """Experiment response for API."""
    id: int
    experiment_key: str
    name: str
    description: Optional[str]
    hypothesis: Optional[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    traffic_percentage: float
    primary_metric: str
    secondary_metrics: list[str]
    min_sample_size: int
    confidence_level: float
    min_detectable_effect: float
    feature_flag_key: Optional[str]
    owner: Optional[str]
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    variants: list[VariantConfig]

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Assignment Schemas
# =============================================================================

class AssignmentContext(BaseModel):
    """Context for experiment assignment."""
    user_id: str = Field(..., min_length=1)
    properties: dict[str, Any] = Field(default_factory=dict)
    pre_experiment_value: Optional[float] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "properties": {"country": "US", "plan": "premium"},
                "pre_experiment_value": 0.15,
            }
        }
    )


class AssignmentResponse(BaseModel):
    """Experiment assignment response."""
    experiment_key: str
    variant_name: str
    is_control: bool
    payload: dict[str, Any]
    already_assigned: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_key": "checkout_flow_v2",
                "variant_name": "treatment",
                "is_control": False,
                "payload": {"button_color": "blue"},
                "already_assigned": False,
            }
        }
    )


class BulkAssignmentRequest(BaseModel):
    """Request multiple experiment assignments."""
    experiment_keys: list[str]
    context: AssignmentContext

    model_config = ConfigDict(extra="forbid")


class BulkAssignmentResponse(BaseModel):
    """Response for bulk assignment."""
    assignments: dict[str, Optional[AssignmentResponse]]
    assignment_time_ms: float


# =============================================================================
# Conversion Schemas
# =============================================================================

class ConversionEvent(BaseModel):
    """Record a conversion event."""
    experiment_key: str
    user_id: str
    metric_name: str
    metric_value: float = Field(default=1.0)
    attribution_window_hours: int = Field(default=24, ge=1, le=168)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_key": "checkout_flow_v2",
                "user_id": "user_123",
                "metric_name": "purchase_completed",
                "metric_value": 1.0,
            }
        }
    )


# =============================================================================
# Results Schemas
# =============================================================================

class VariantResult(BaseModel):
    """Results for a single variant."""
    variant_name: str
    sample_size: int
    conversions: int
    conversion_rate: float
    mean_value: Optional[float]
    std_dev: Optional[float]

    # Comparison to control (null for control)
    relative_lift: Optional[float]
    absolute_lift: Optional[float]

    # Statistical significance
    p_value: Optional[float]
    confidence_interval: Optional[tuple[float, float]]
    is_significant: bool

    # Bayesian results
    probability_of_being_best: Optional[float]
    expected_loss: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class ExperimentResults(BaseModel):
    """Full experiment results."""
    experiment_key: str
    status: str
    primary_metric: str
    total_sample_size: int
    variants: list[VariantResult]

    # Summary
    winner: Optional[str]  # Variant name or None if no clear winner
    recommendation: str  # "continue", "stop_winner", "stop_no_effect"

    # Power analysis
    achieved_power: Optional[float]
    days_remaining: Optional[int]

    computed_at: datetime


class SampleSizeCalculation(BaseModel):
    """Sample size calculation request."""
    baseline_rate: float = Field(..., gt=0, lt=1)
    minimum_detectable_effect: float = Field(..., gt=0, lt=1)
    power: float = Field(default=0.8, ge=0.5, le=0.99)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)


class SampleSizeResponse(BaseModel):
    """Sample size calculation response."""
    required_sample_size_per_variant: int
    total_sample_size: int
    baseline_rate: float
    minimum_detectable_effect: float
    power: float
    confidence_level: float
