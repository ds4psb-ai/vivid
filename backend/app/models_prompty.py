"""Prompty Project & Workflow Models.

Models for prompty.co.kr - AI-free guide platform.
Users follow step-by-step workflows using Gemini CLI + Antigravity.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Float, Text, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PromptyProject(Base):
    """User's workflow project.

    Each project follows a template workflow with multiple stages.
    State is synced with STATE.md via Yjs CRDT.
    """
    __tablename__ = "prompty_projects"
    __table_args__ = (
        Index("ix_prompty_projects_user", "user_id"),
        Index("ix_prompty_projects_template", "template_id"),
        Index("ix_prompty_projects_status", "status"),
        Index("ix_prompty_projects_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Owner
    user_id: Mapped[str] = mapped_column(String(160))

    # Template source (nullable = from scratch)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Workflow state (Yjs-compatible)
    state: Mapped[dict] = mapped_column(JSONB, default=dict)
    """
    STATE.md-compatible structure:
    {
        "stages": {
            "analysis": {"status": "completed", "files": ["analysis.md"]},
            "image": {
                "anchor_girl": {"status": "in_progress", "version": 2},
                "scenes": {
                    "scene_1": {"status": "pending"},
                }
            },
            "video": {},
            "assembly": {}
        },
        "current_step": "image.anchor_girl",
        "last_activity": "2026-02-02T10:00:00Z"
    }
    """

    # Current workflow position
    current_stage: Mapped[str] = mapped_column(String(64), default="analysis")
    current_step: Mapped[str] = mapped_column(String(128), default="")

    # Progress tracking
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    # Status
    status: Mapped[str] = mapped_column(String(32), default="active")
    # active, paused, completed, archived

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    critiques: Mapped[list["PromptyCritique"]] = relationship(
        "PromptyCritique",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class PromptyTemplate(Base):
    """Workflow template for the marketplace.

    Migrated from viral-video-automation/templates/.
    Each template defines stages, steps, and critique checklists.
    """
    __tablename__ = "prompty_templates"
    __table_args__ = (
        Index("ix_prompty_templates_category", "category"),
        Index("ix_prompty_templates_featured", "is_featured"),
        Index("ix_prompty_templates_use_count", "use_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Creator (admin or verified user)
    creator_id: Mapped[str] = mapped_column(String(160))
    creator_name: Mapped[str] = mapped_column(String(100), default="Prompty Team")

    # Category
    category: Mapped[str] = mapped_column(String(64), default="video")
    # video, image, audio, social, marketing

    # Workflow definition
    workflow_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    """
    {
        "stages": ["analysis", "image", "video", "assembly"],
        "steps": {
            "analysis": [
                {"id": "analyze_reference", "name": "레퍼런스 분석", "prompt_file": "prompts/analysis.md"},
            ],
            "image": [
                {"id": "anchor_girl", "name": "앵커 걸", "prompt_template": "..."},
                {"id": "anchor_boy", "name": "앵커 보이", "prompt_template": "..."},
            ]
        },
        "critique_checklist": [
            {"id": "composition", "name": "구도", "weight": 0.15},
            {"id": "consistency", "name": "일관성", "weight": 0.20},
        ]
    }
    """

    # Critique checklist (for quality scoring)
    critique_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    """
    {
        "items": [
            {"id": "composition", "label": "구도", "description": "...", "weight": 0.15},
            ...
        ],
        "passing_score": 75
    }
    """

    # Example project (optional reference)
    example_project_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Tags
    tags: Mapped[list] = mapped_column(JSONB, default=list)

    # Statistics
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_sum: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    # Curation
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def rating_avg(self) -> float:
        """Calculate average rating."""
        if self.rating_count == 0:
            return 0.0
        return round(self.rating_sum / self.rating_count, 1)


class PromptyCritique(Base):
    """Quality critique for a project step.

    Users submit critique scores after completing each step.
    Based on CRITIQUE_*.md checklists from viral-video-automation.
    """
    __tablename__ = "prompty_critiques"
    __table_args__ = (
        Index("ix_prompty_critiques_project", "project_id"),
        Index("ix_prompty_critiques_stage", "stage"),
        Index("ix_prompty_critiques_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent project
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompty_projects.id", ondelete="CASCADE"),
    )

    # Stage & Step
    stage: Mapped[str] = mapped_column(String(64))  # analysis, image, video, assembly
    step_id: Mapped[str] = mapped_column(String(128))  # anchor_girl, scene_1, etc.

    # Critique scores (checklist-based)
    scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    """
    {
        "composition": {"score": 8, "notes": "..."},
        "consistency": {"score": 9, "notes": "..."},
        ...
    }
    """

    # Calculated total score
    total_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100

    # Pass/Fail (based on template's passing_score)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Revision tracking
    revision_number: Mapped[int] = mapped_column(Integer, default=1)

    # Optional notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    project: Mapped["PromptyProject"] = relationship(
        "PromptyProject",
        back_populates="critiques",
    )


class PromptyGuideLog(Base):
    """Activity log for workflow guide.

    Tracks user progress through the guide for analytics.
    """
    __tablename__ = "prompty_guide_logs"
    __table_args__ = (
        Index("ix_prompty_guide_logs_project", "project_id"),
        Index("ix_prompty_guide_logs_action", "action"),
        Index("ix_prompty_guide_logs_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent project
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[str] = mapped_column(String(160))

    # Action
    action: Mapped[str] = mapped_column(String(64))
    # copy_prompt, open_external, complete_step, submit_critique, next_stage

    # Context
    stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    step_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Extra data
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
