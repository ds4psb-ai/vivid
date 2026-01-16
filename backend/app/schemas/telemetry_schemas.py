"""Telemetry Pydantic Schemas for API validation.

Comprehensive schemas with full validation for the telemetry system.
"""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# Enums as Literals for API
# =============================================================================

ToolTierLiteral = Literal["experimental", "verified", "certified"]
SafetyRatingLiteral = Literal["safe", "review", "restricted"]
RunStatusLiteral = Literal["started", "success", "failed", "timeout"]
MetricTypeLiteral = Literal["counter", "gauge", "histogram"]
PeriodTypeLiteral = Literal["hourly", "daily", "weekly", "monthly"]


# =============================================================================
# Tool Manifest Schemas
# =============================================================================

class ToolManifestCreate(BaseModel):
    """Create a new tool manifest."""
    tool_key: str = Field(..., min_length=3, max_length=160, pattern=r"^[a-z0-9_-]+$")
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(..., min_length=1, max_length=64)
    
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    credit_cost: int = Field(default=1, ge=0, le=1000)
    
    # AI system prompt for LLM-powered tools (stored securely in ToolSchema)
    system_prompt: Optional[str] = Field(None, min_length=20, max_length=10000)
    
    # Optional fork info
    parent_tool_id: Optional[UUID] = None
    
    @field_validator("tool_key")
    @classmethod
    def validate_tool_key(cls, v: str) -> str:
        """Ensure tool_key is lowercase and valid."""
        return v.lower().strip()
    
    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Normalize category."""
        return v.lower().strip()


class ToolManifestUpdate(BaseModel):
    """Update an existing tool manifest."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    credit_cost: Optional[int] = Field(None, ge=0, le=1000)
    is_active: Optional[bool] = None


class ToolManifestResponse(BaseModel):
    """Tool manifest API response."""
    id: UUID
    tool_key: str
    display_name: str
    description: str
    version: str
    category: str
    tier: ToolTierLiteral
    
    input_schema: dict
    output_schema: dict
    credit_cost: int
    
    fork_count: int
    usage_count: int
    total_revenue: int
    
    parent_tool_id: Optional[UUID] = None
    fork_depth: int
    
    created_by: str
    approved_at: Optional[datetime] = None
    safety_rating: SafetyRatingLiteral
    sandbox_required: bool
    is_active: bool
    
    test_pass_rate: Optional[float] = None
    quality_rating: Optional[float] = None
    human_cloud_success_rate: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Tool Run Event Schemas
# =============================================================================

class ToolRunEventCreate(BaseModel):
    """Record a new tool run event."""
    tool_id: UUID
    tool_key: str = Field(..., max_length=160)
    tool_version: str = Field(default="1.0.0", max_length=32)
    
    user_id: Optional[str] = Field(None, max_length=160)
    session_id: Optional[UUID] = None
    
    inputs_summary: dict = Field(default_factory=dict)
    
    # Optional context
    canvas_id: Optional[UUID] = None
    workflow_position: Optional[int] = Field(None, ge=0)
    previous_tool_id: Optional[UUID] = None
    
    @field_validator("inputs_summary")
    @classmethod
    def sanitize_inputs(cls, v: dict) -> dict:
        """Remove any potential PII from inputs summary."""
        # Remove known PII fields
        pii_fields = {"password", "secret", "api_key", "token", "credit_card", "ssn"}
        return {k: v for k, v in v.items() if k.lower() not in pii_fields}


class ToolRunEventComplete(BaseModel):
    """Complete a tool run event with results."""
    status: RunStatusLiteral
    outputs_summary: dict = Field(default_factory=dict)
    error_message: Optional[str] = Field(None, max_length=2000)
    
    latency_ms: Optional[int] = Field(None, ge=0)
    token_usage: dict = Field(default_factory=dict)
    cost_usd_est: Optional[float] = Field(None, ge=0)
    
    credits_charged: int = Field(default=0, ge=0)
    credits_refunded: int = Field(default=0, ge=0)


class ToolRunEventResponse(BaseModel):
    """Tool run event API response."""
    id: UUID
    tool_id: UUID
    tool_key: str
    tool_version: str
    
    user_id: Optional[str] = None
    session_id: Optional[UUID] = None
    
    status: str
    inputs_summary: dict
    outputs_summary: dict
    error_message: Optional[str] = None
    
    latency_ms: Optional[int] = None
    token_usage: dict
    cost_usd_est: Optional[float] = None
    
    credits_charged: int
    credits_refunded: int
    
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    
    canvas_id: Optional[UUID] = None
    workflow_position: Optional[int] = None
    previous_tool_id: Optional[UUID] = None
    
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ToolRunFeedback(BaseModel):
    """User feedback for a tool run."""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=1000)


# =============================================================================
# Fork Event Schemas
# =============================================================================

class ForkEventCreate(BaseModel):
    """Create a new fork event."""
    parent_tool_id: UUID
    child_tool_id: UUID
    forker_id: str = Field(..., max_length=160)
    fork_reason: Optional[str] = Field(None, max_length=500)
    
    # Diff analysis
    diff_lines_added: int = Field(default=0, ge=0)
    diff_lines_removed: int = Field(default=0, ge=0)
    diff_lines_modified: int = Field(default=0, ge=0)
    
    @model_validator(mode="after")
    def calculate_diff_score(self):
        """Calculate normalized diff score based on changes."""
        total_changes = self.diff_lines_added + self.diff_lines_removed + self.diff_lines_modified
        # Normalize to 0-100 (sigmoid-like curve)
        if total_changes == 0:
            return self
        # More changes = higher score, but with diminishing returns
        # Score approaches 100 as changes increase
        import math
        self.__dict__["diff_score"] = min(100, 100 * (1 - math.exp(-total_changes / 50)))
        return self


class ForkEventResponse(BaseModel):
    """Fork event API response."""
    id: UUID
    parent_tool_id: UUID
    child_tool_id: UUID
    fork_depth: int
    
    forker_id: str
    fork_reason: Optional[str] = None
    
    diff_lines_added: int
    diff_lines_removed: int
    diff_lines_modified: int
    diff_score: float
    
    test_passed: bool
    test_run_at: Optional[datetime] = None
    
    attribution_score: float
    attribution_calculated_at: Optional[datetime] = None
    
    revenue_generated: int
    revenue_shared: int
    
    is_suspicious: bool
    suspicion_reason: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForkTestResult(BaseModel):
    """Submit test results for a fork."""
    test_passed: bool
    test_details: dict = Field(default_factory=dict)


# =============================================================================
# Metric Event Schemas
# =============================================================================

class MetricEventCreate(BaseModel):
    """Create or update a metric event."""
    metric_key: str = Field(..., max_length=120)
    metric_type: MetricTypeLiteral
    
    period_start: datetime
    period_end: datetime
    period_type: PeriodTypeLiteral
    
    dimension_type: str = Field(..., max_length=64)
    dimension_value: str = Field(..., max_length=200)
    
    count: int = Field(default=0, ge=0)
    sum_value: float = Field(default=0.0)
    avg_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    p50_value: Optional[float] = None
    p95_value: Optional[float] = None
    p99_value: Optional[float] = None
    
    breakdown: dict = Field(default_factory=dict)
    meta: dict = Field(default_factory=dict)
    
    @model_validator(mode="after")
    def validate_period(self):
        """Ensure period_start is before period_end."""
        if self.period_start >= self.period_end:
            raise ValueError("period_start must be before period_end")
        return self


class MetricEventResponse(BaseModel):
    """Metric event API response."""
    id: UUID
    metric_key: str
    metric_type: str
    
    period_start: datetime
    period_end: datetime
    period_type: str
    
    dimension_type: str
    dimension_value: str
    
    count: int
    sum_value: float
    avg_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    p50_value: Optional[float] = None
    p95_value: Optional[float] = None
    p99_value: Optional[float] = None
    
    breakdown: dict
    meta: dict
    
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Attribution Score Calculation Schema
# =============================================================================

class AttributionScoreRequest(BaseModel):
    """Request to calculate attribution score for a fork."""
    fork_id: UUID


class AttributionScoreResponse(BaseModel):
    """Attribution score calculation result."""
    fork_id: UUID
    tool_id: UUID
    
    # Component scores (0-100 each)
    diff_score: float = Field(..., ge=0, le=100)
    test_score: float = Field(..., ge=0, le=100)
    usage_score: float = Field(..., ge=0, le=100)
    revenue_score: float = Field(..., ge=0, le=100)
    quality_score: float = Field(..., ge=0, le=100)
    
    # Final weighted score
    total_score: float = Field(..., ge=0, le=100)
    
    # Weights used
    weights: dict = Field(default_factory=lambda: {
        "diff": 0.2,
        "test": 0.15,
        "usage": 0.25,
        "revenue": 0.25,
        "quality": 0.15,
    })
    
    calculated_at: datetime


# =============================================================================
# Tool Analytics Schemas
# =============================================================================

class ToolAnalytics(BaseModel):
    """Analytics summary for a tool."""
    tool_id: UUID
    tool_key: str
    
    # Usage stats
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    
    # Performance
    avg_latency_ms: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    
    # Economics
    total_credits_earned: int
    total_credits_refunded: int
    net_revenue: int
    
    # Quality
    avg_rating: Optional[float] = None
    rating_count: int
    
    # Fork info
    fork_count: int
    forked_from: Optional[str] = None
    
    # Period
    period_start: datetime
    period_end: datetime


class CategoryAnalytics(BaseModel):
    """Analytics summary for a category."""
    category: str
    
    tool_count: int
    total_runs: int
    avg_success_rate: float
    
    total_revenue: int
    avg_tool_revenue: float
    
    top_tools: list[str]
    trending_tools: list[str]
    
    period_start: datetime
    period_end: datetime
