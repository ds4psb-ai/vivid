"""
Feature Flag Pydantic Schemas (2026 Best Practice)

Uses Pydantic v2 ConfigDict pattern (not deprecated class Config).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class FeatureContext(BaseModel):
    """
    Context for feature flag evaluation.

    2026 Best Practice:
    - userId for user-specific targeting
    - properties for attribute-based targeting
    - environment for env-specific flags
    """
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    environment: str = Field(default="production", description="Environment name")
    properties: dict[str, Any] = Field(default_factory=dict, description="Custom properties for targeting")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "environment": "production",
                "properties": {
                    "plan": "premium",
                    "country": "KR",
                    "beta_tester": True,
                }
            }
        }
    )


class StrategyConfig(BaseModel):
    """Targeting strategy configuration."""
    user_ids: list[str] = Field(default_factory=list, description="Specific user IDs to target")
    percentage: Optional[float] = Field(default=None, ge=0, le=100, description="Percentage rollout (0-100)")
    properties: dict[str, Any] = Field(default_factory=dict, description="Property-based targeting rules")
    environments: list[str] = Field(default_factory=list, description="Target environments")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_ids": ["admin-1", "beta-user-2"],
                "percentage": 25.0,
                "properties": {"plan": "premium"},
                "environments": ["production", "staging"],
            }
        }
    )


class VariantConfig(BaseModel):
    """Variant configuration for multivariate flags."""
    name: str = Field(description="Variant name")
    weight: float = Field(ge=0, le=100, description="Weight percentage (0-100)")
    payload: Optional[dict[str, Any]] = Field(default=None, description="Optional payload data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "variant_a",
                "weight": 50,
                "payload": {"color": "blue", "size": "large"},
            }
        }
    )


class FeatureFlagCreate(BaseModel):
    """Request to create a feature flag."""
    flag_key: str = Field(max_length=255, pattern=r"^[a-z][a-z0-9_]*$", description="Unique flag key (snake_case)")
    name: str = Field(max_length=255, description="Display name")
    description: Optional[str] = Field(default=None, description="Flag description")
    enabled: bool = Field(default=False, description="Global enable/disable")
    strategies: StrategyConfig = Field(default_factory=StrategyConfig, description="Targeting strategies")
    variants: list[VariantConfig] = Field(default_factory=list, description="Multivariate variants")
    default_variant: str = Field(default="off", description="Default variant when no match")
    tags: list[str] = Field(default_factory=list, description="Tags for organization")
    owner: Optional[str] = Field(default=None, description="Flag owner")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flag_key": "new_checkout_flow",
                "name": "New Checkout Flow",
                "description": "Enable redesigned checkout experience",
                "enabled": True,
                "strategies": {
                    "percentage": 10,
                    "properties": {"plan": "premium"},
                },
                "tags": ["checkout", "experiment"],
            }
        }
    )


class FeatureFlagUpdate(BaseModel):
    """Request to update a feature flag."""
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    enabled: Optional[bool] = Field(default=None)
    strategies: Optional[StrategyConfig] = Field(default=None)
    variants: Optional[list[VariantConfig]] = Field(default=None)
    default_variant: Optional[str] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    owner: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None, description="Reason for change (audit)")


class FeatureFlagResponse(BaseModel):
    """Feature flag response."""
    id: int
    flag_key: str
    name: str
    description: Optional[str]
    enabled: bool
    status: str
    strategies: dict[str, Any]
    variants: list[dict[str, Any]]
    default_variant: str
    tags: list[str]
    owner: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureFlagEvaluation(BaseModel):
    """Result of feature flag evaluation."""
    flag_key: str
    enabled: bool
    variant: str
    reason: Literal["default", "user_targeted", "percentage_rollout", "property_match", "disabled", "not_found"]
    evaluation_time_ms: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flag_key": "new_checkout_flow",
                "enabled": True,
                "variant": "variant_a",
                "reason": "percentage_rollout",
                "evaluation_time_ms": 0.5,
            }
        }
    )


class BulkEvaluationRequest(BaseModel):
    """Request to evaluate multiple flags at once."""
    flag_keys: list[str] = Field(description="List of flag keys to evaluate")
    context: FeatureContext = Field(description="Evaluation context")


class BulkEvaluationResponse(BaseModel):
    """Response for bulk flag evaluation."""
    evaluations: dict[str, FeatureFlagEvaluation]
    evaluation_time_ms: float
