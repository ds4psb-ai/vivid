"""
A/B Testing SQLAlchemy Models (2026 Best Practice)

Tables:
- experiments: Experiment definitions
- experiment_variants: Variant configurations
- experiment_exposures: User exposure tracking
- experiment_conversions: Conversion events
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    Integer,
    Float,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ExperimentStatus(str, enum.Enum):
    """Experiment lifecycle status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Experiment(Base):
    """
    Experiment definition.

    2026 Best Practice:
    - Clear hypothesis and success metrics
    - Proper sample size calculation
    - Sequential testing support
    """
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_key = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=True)

    # Status and timing
    status = Column(SQLEnum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Traffic allocation (0-100%)
    traffic_percentage = Column(Float, default=100.0, nullable=False)

    # Metrics configuration
    primary_metric = Column(String(255), nullable=False)  # e.g., "conversion_rate", "revenue"
    secondary_metrics = Column(JSON, default=list, nullable=False)  # ["time_on_page", "clicks"]

    # Statistical settings
    min_sample_size = Column(Integer, default=1000, nullable=False)
    confidence_level = Column(Float, default=0.95, nullable=False)  # 95%
    min_detectable_effect = Column(Float, default=0.05, nullable=False)  # 5%

    # Feature flag integration
    feature_flag_key = Column(String(255), nullable=True)  # Link to feature flag

    # Metadata
    owner = Column(String(255), nullable=True)
    tags = Column(JSON, default=list, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    variants = relationship("ExperimentVariant", back_populates="experiment", lazy="selectin")
    exposures = relationship("ExperimentExposure", back_populates="experiment", lazy="dynamic")
    conversions = relationship("ExperimentConversion", back_populates="experiment", lazy="dynamic")

    __table_args__ = (
        Index("ix_experiments_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Experiment {self.experiment_key} status={self.status}>"


class ExperimentVariant(Base):
    """
    Experiment variant configuration.

    Each experiment has 2+ variants (control + treatments).
    """
    __tablename__ = "experiment_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    name = Column(String(100), nullable=False)  # "control", "treatment_a", etc.
    description = Column(Text, nullable=True)

    # Traffic weight (relative, sums to 100 across variants)
    weight = Column(Float, nullable=False)

    # Optional payload for variant-specific config
    payload = Column(JSON, default=dict, nullable=False)

    # Is this the control group?
    is_control = Column(Boolean, default=False, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="variants")

    __table_args__ = (
        UniqueConstraint("experiment_id", "name", name="uq_experiment_variant"),
    )

    def __repr__(self) -> str:
        return f"<ExperimentVariant {self.name} weight={self.weight}>"


class ExperimentExposure(Base):
    """
    User exposure to experiment.

    Tracks when a user was assigned to an experiment variant.
    2026 Best Practice: Only count users who actually see the experiment.
    """
    __tablename__ = "experiment_exposures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    variant_name = Column(String(100), nullable=False)

    # Assignment metadata
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    context = Column(JSON, default=dict, nullable=False)  # User context at assignment

    # For CUPED variance reduction
    pre_experiment_value = Column(Float, nullable=True)

    # Relationships
    experiment = relationship("Experiment", back_populates="exposures")

    __table_args__ = (
        UniqueConstraint("experiment_id", "user_id", name="uq_experiment_user"),
        Index("ix_experiment_exposures_variant", "experiment_id", "variant_name"),
    )

    def __repr__(self) -> str:
        return f"<ExperimentExposure user={self.user_id} variant={self.variant_name}>"


class ExperimentConversion(Base):
    """
    Conversion event for experiment.

    Tracks when a user completes a success metric.
    """
    __tablename__ = "experiment_conversions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    variant_name = Column(String(100), nullable=False)

    # Metric details
    metric_name = Column(String(255), nullable=False)  # e.g., "purchase", "signup"
    metric_value = Column(Float, default=1.0, nullable=False)  # For continuous metrics

    # Timing
    converted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Attribution
    attribution_window_hours = Column(Integer, default=24, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="conversions")

    __table_args__ = (
        Index("ix_experiment_conversions_metric", "experiment_id", "metric_name"),
        Index("ix_experiment_conversions_variant", "experiment_id", "variant_name"),
    )

    def __repr__(self) -> str:
        return f"<ExperimentConversion user={self.user_id} metric={self.metric_name}>"


class ExperimentResult(Base):
    """
    Cached experiment results for dashboard.

    Computed periodically from exposures and conversions.
    """
    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    variant_name = Column(String(100), nullable=False)
    metric_name = Column(String(255), nullable=False)

    # Sample statistics
    sample_size = Column(Integer, default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    conversion_rate = Column(Float, nullable=True)
    mean_value = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)

    # Comparison to control
    relative_lift = Column(Float, nullable=True)  # % change vs control
    absolute_lift = Column(Float, nullable=True)

    # Statistical significance
    p_value = Column(Float, nullable=True)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    is_significant = Column(Boolean, default=False, nullable=False)

    # Bayesian results
    probability_of_being_best = Column(Float, nullable=True)
    expected_loss = Column(Float, nullable=True)

    # Metadata
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("experiment_id", "variant_name", "metric_name", name="uq_experiment_result"),
    )
