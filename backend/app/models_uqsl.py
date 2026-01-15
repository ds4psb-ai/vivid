"""
UQSL SQLAlchemy Models - Universal Quality Selection Layer

Database models for Thompson Sampling, configuration, and selection history.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BanditArm(Base):
    """
    Thompson Sampling Arm (Beta Distribution)

    Tracks success/failure counts for each arm in the multi-armed bandit.
    Alpha and Beta parameters follow the Beta distribution:
    - alpha: success count + 1 (prior)
    - beta: failure count + 1 (prior)
    """
    __tablename__ = "bandit_arms"

    arm_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    arm_type: Mapped[str] = mapped_column(String(50), nullable=False)  # backend, reranker, generation, ensemble

    # Beta distribution parameters (initialized to 1,1 = uniform prior)
    alpha: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    beta: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_trials: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Last observed reward
    last_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<BanditArm {self.arm_id} α={self.alpha} β={self.beta}>"

    @property
    def success_rate(self) -> float:
        """Expected success rate (mean of Beta distribution)"""
        return self.alpha / (self.alpha + self.beta)

    @property
    def confidence(self) -> float:
        """Confidence based on number of trials"""
        if self.total_trials == 0:
            return 0.0
        return 1 - (1 / (self.total_trials + 1))


class UQSLConfig(Base):
    """
    App-level UQSL Configuration

    Stores per-app settings for quality selection layer.
    """
    __tablename__ = "uqsl_configs"

    app_key: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Generation settings
    n_candidates: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    selection_strategy: Mapped[str] = mapped_column(
        String(20), default="auto", nullable=False
    )  # auto, hitl, hybrid, llm_judge

    # Quality weights (JSONB)
    quality_weights: Mapped[dict] = mapped_column(
        JSONB,
        default={
            "groundedness": 0.30,
            "relevance": 0.25,
            "coherence": 0.20,
            "creativity": 0.15,
            "safety": 0.10,
        },
    )

    # Bandit arms for this app
    bandit_arms: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=["backend:qdrant_hybrid", "backend:notebooklm"],
    )

    # Tier and feature flags
    tier: Mapped[str] = mapped_column(String(20), default="free", nullable=False)  # free, premium, dev
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Thresholds
    auto_threshold: Mapped[float] = mapped_column(Float, default=0.85)
    top_k_for_hitl: Mapped[int] = mapped_column(Integer, default=2)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<UQSLConfig {self.app_key} tier={self.tier}>"


class SelectionHistory(Base):
    """
    Selection Audit Log

    Records all UQSL selection events for analytics and feedback tracking.
    """
    __tablename__ = "selection_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    app_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Query information
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prompt_preview: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Generation details
    n_candidates: Mapped[int] = mapped_column(Integer, nullable=False)
    candidates_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    quality_scores: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Selection details
    selected_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_method: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # auto, hitl, hybrid, llm_judge
    selection_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Thompson Sampling tracking
    arms_used: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    # User feedback (updated later)
    user_feedback: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )  # positive, negative
    feedback_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Performance metrics
    total_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generation_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evaluation_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Context
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dimension: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<SelectionHistory {self.id} app={self.app_key} method={self.selection_method}>"


class EnsembleComparison(Base):
    """
    Ensemble++ 3-Way Comparison Results

    Records results from NeurIPS 2025 3-way comparison framework (A vs B vs A+B).
    """
    __tablename__ = "ensemble_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Query
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    dimension: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    auteur_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # 3-way results
    result_a: Mapped[dict] = mapped_column(JSONB, nullable=False)   # Qdrant only
    result_b: Mapped[dict] = mapped_column(JSONB, nullable=False)   # NotebookLM only
    result_ab: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Ensemble merged

    # Selection
    recommended: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # a, b, ab
    user_selected: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # a, b, ab, skip
    selection_match: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Thompson Sampling snapshots
    arms_stats_before: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    arms_stats_after: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Context
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<EnsembleComparison {self.id} rec={self.recommended} sel={self.user_selected}>"
