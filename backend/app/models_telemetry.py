"""Telemetry DB Models for 4-Layer Ecosystem.

Tracks tool usage, fork events, and metrics for collective intelligence.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Float, Text, Index, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class ToolTier(str, enum.Enum):
    """Tool verification tier levels."""
    EXPERIMENTAL = "experimental"  # Anyone can create, limited search exposure
    VERIFIED = "verified"          # Passed automated tests
    CERTIFIED = "certified"        # Proven Human Cloud success rate


class EventStatus(str, enum.Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


# =============================================================================
# Tool Manifest - Source of Record for all tools
# =============================================================================

class ToolManifest(Base):
    """Tool definition and governance metadata.
    
    This is the Source of Record (SoR) for all tools in the ecosystem.
    MCP reads from this table to expose tools to external agents.
    """
    __tablename__ = "tool_manifests"
    __table_args__ = (
        Index("ix_tool_manifests_tool_key", "tool_key"),
        Index("ix_tool_manifests_tier", "tier"),
        Index("ix_tool_manifests_category", "category"),
        Index("ix_tool_manifests_created_by", "created_by"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_key: Mapped[str] = mapped_column(String(160), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    
    # Category and tier
    category: Mapped[str] = mapped_column(String(64))  # film, tarot, design, etc.
    tier: Mapped[str] = mapped_column(String(32), default=ToolTier.EXPERIMENTAL.value)
    
    # Schema definitions
    input_schema: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_schema: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Economics
    credit_cost: Mapped[int] = mapped_column(Integer, default=1)
    fork_count: Mapped[int] = mapped_column(Integer, default=0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[int] = mapped_column(Integer, default=0)  # Credits earned
    
    # Fork lineage
    parent_tool_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    fork_depth: Mapped[int] = mapped_column(Integer, default=0)
    
    # Governance
    created_by: Mapped[str] = mapped_column(String(160))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    safety_rating: Mapped[str] = mapped_column(String(32), default="safe")  # safe, review, restricted
    sandbox_required: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Metrics for tier promotion
    test_pass_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 1-5 stars
    human_cloud_success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Tool Run Event - Every tool execution
# =============================================================================

class ToolRunEvent(Base):
    """Tracks every tool execution for analytics and attribution.
    
    This is the core telemetry table for:
    - Usage analytics
    - Attribution score calculation
    - Collective intelligence patterns
    """
    __tablename__ = "tool_run_events"
    __table_args__ = (
        Index("ix_tool_run_events_tool_key", "tool_key"),
        Index("ix_tool_run_events_user_id", "user_id"),
        Index("ix_tool_run_events_created_at", "created_at"),
        Index("ix_tool_run_events_status", "status"),
        Index("ix_tool_run_events_tool_created", "tool_key", "created_at"),  # Composite for tool analytics
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tool reference
    tool_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    tool_key: Mapped[str] = mapped_column(String(160))
    tool_version: Mapped[str] = mapped_column(String(32))
    
    # User context
    user_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Execution details
    status: Mapped[str] = mapped_column(String(32), default="started")  # started, success, failed, timeout
    inputs_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA256 of inputs for dedup
    inputs_summary: Mapped[dict] = mapped_column(JSONB, default=dict)  # Sanitized input summary (no PII)
    outputs_summary: Mapped[dict] = mapped_column(JSONB, default=dict)  # Sanitized output summary
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Performance metrics
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict] = mapped_column(JSONB, default=dict)  # {input: x, output: y}
    cost_usd_est: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Credits
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)
    credits_refunded: Mapped[int] = mapped_column(Integer, default=0)
    
    # Quality feedback (filled later via feedback API)
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context for collective intelligence
    canvas_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    workflow_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Order in workflow
    previous_tool_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# =============================================================================
# Fork Event - Tool derivation tracking
# =============================================================================

class ForkEvent(Base):
    """Tracks every fork creation for attribution and revenue sharing.
    
    Used to:
    - Calculate attribution scores
    - Distribute fork revenue (Attribution-based, not depth-based)
    - Detect Sybil attacks
    """
    __tablename__ = "fork_events"
    __table_args__ = (
        Index("ix_fork_events_parent_tool_id", "parent_tool_id"),
        Index("ix_fork_events_child_tool_id", "child_tool_id"),
        Index("ix_fork_events_forker_id", "forker_id"),
        Index("ix_fork_events_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Fork relationship
    parent_tool_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    child_tool_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    fork_depth: Mapped[int] = mapped_column(Integer, default=1)  # Distance from original
    
    # Forker info
    forker_id: Mapped[str] = mapped_column(String(160))
    fork_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Change analysis (for attribution score)
    diff_lines_added: Mapped[int] = mapped_column(Integer, default=0)
    diff_lines_removed: Mapped[int] = mapped_column(Integer, default=0)
    diff_lines_modified: Mapped[int] = mapped_column(Integer, default=0)
    diff_score: Mapped[float] = mapped_column(Float, default=0.0)  # Normalized 0-100
    
    # Test results
    test_passed: Mapped[bool] = mapped_column(default=False)
    test_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    test_details: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Attribution score (calculated asynchronously)
    attribution_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    attribution_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Revenue sharing (accumulated over time)
    revenue_generated: Mapped[int] = mapped_column(Integer, default=0)  # Total credits from this fork
    revenue_shared: Mapped[int] = mapped_column(Integer, default=0)  # Credits shared with parent chain
    
    # Anti-Sybil checks
    is_suspicious: Mapped[bool] = mapped_column(default=False)
    suspicion_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Metric Event - Aggregated metrics for dashboards
# =============================================================================

class MetricEvent(Base):
    """Aggregated metrics for analytics dashboards and RAG recommendations.
    
    Pre-computed aggregates for:
    - Tool popularity rankings
    - Category trends
    - Collective intelligence patterns
    """
    __tablename__ = "metric_events"
    __table_args__ = (
        Index("ix_metric_events_metric_key", "metric_key"),
        Index("ix_metric_events_period", "period_start", "period_end"),
        Index("ix_metric_events_dimension", "dimension_type", "dimension_value"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric identification
    metric_key: Mapped[str] = mapped_column(String(120))  # e.g., "tool_usage", "fork_count", "revenue"
    metric_type: Mapped[str] = mapped_column(String(32))  # counter, gauge, histogram
    
    # Time period
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    period_type: Mapped[str] = mapped_column(String(16))  # hourly, daily, weekly, monthly
    
    # Dimension (what this metric is about)
    dimension_type: Mapped[str] = mapped_column(String(64))  # tool, category, user, workflow
    dimension_value: Mapped[str] = mapped_column(String(200))  # tool_key, category name, etc.
    
    # Metric values
    count: Mapped[int] = mapped_column(Integer, default=0)
    sum_value: Mapped[float] = mapped_column(Float, default=0.0)
    avg_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p50_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Median
    p95_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p99_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Additional context
    breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)  # Sub-breakdowns
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Tool Workflow Pattern - For collective intelligence
# =============================================================================

class ToolWorkflowPattern(Base):
    """Common tool combination patterns for RAG recommendations.
    
    Tracks which tools are commonly used together.
    """
    __tablename__ = "tool_workflow_patterns"
    __table_args__ = (
        Index("ix_workflow_patterns_pattern_key", "pattern_key"),
        Index("ix_workflow_patterns_frequency", "frequency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Pattern identification
    pattern_key: Mapped[str] = mapped_column(String(200), unique=True)  # Hash of tool sequence
    tool_sequence: Mapped[list] = mapped_column(JSONB)  # Ordered list of tool_keys
    
    # Statistics
    frequency: Mapped[int] = mapped_column(Integer, default=1)
    avg_completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_user_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Context
    common_categories: Mapped[list] = mapped_column(JSONB, default=list)  # Which categories use this
    common_use_cases: Mapped[list] = mapped_column(JSONB, default=list)  # Inferred use cases
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
