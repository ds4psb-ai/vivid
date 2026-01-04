"""Blackhole Template Models.

Models for managing curated workflow templates (블랙홀 갤러리).
Stores best-practice templates derived from successful dimension app executions.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, DateTime, Integer, Float, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BlackholeTemplate(Base):
    """Curated workflow template for the Blackhole Gallery.
    
    Represents a best-practice template that users can apply 
    to quickly start their dimension workflow.
    """
    __tablename__ = "blackhole_templates"
    __table_args__ = (
        Index("ix_blackhole_templates_dimension", "dimension_source"),
        Index("ix_blackhole_templates_is_featured", "is_featured"),
        Index("ix_blackhole_templates_use_count", "use_count"),
        Index("ix_blackhole_templates_creator", "creator_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Creator
    creator_id: Mapped[str] = mapped_column(String(160))
    creator_name: Mapped[str] = mapped_column(String(100), default="Anonymous")
    
    # Dimension source (1D, 2D, 3D, 4D)
    dimension_source: Mapped[str] = mapped_column(String(32))
    
    # Workflow definition
    tool_sequence: Mapped[list] = mapped_column(JSONB, default=list)  # ["1D", "2D", "3D"]
    input_preset: Mapped[dict] = mapped_column(JSONB, default=dict)  # Pre-filled inputs
    output_example: Mapped[dict] = mapped_column(JSONB, default=dict)  # Example output
    
    # Categorization
    tags: Mapped[list] = mapped_column(JSONB, default=list)  # ["cinematic", "veo", "prompt"]
    category: Mapped[str] = mapped_column(String(64), default="general")
    
    # Statistics
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_sum: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Curation
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def rating_avg(self) -> float:
        """Calculate average rating."""
        if self.rating_count == 0:
            return 0.0
        return round(self.rating_sum / self.rating_count, 1)


class BlackholeUsage(Base):
    """Tracks when users apply a template from the Blackhole gallery."""
    __tablename__ = "blackhole_usages"
    __table_args__ = (
        Index("ix_blackhole_usages_template", "template_id"),
        Index("ix_blackhole_usages_user", "user_id"),
        Index("ix_blackhole_usages_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[str] = mapped_column(String(160))
    
    # Optional rating after use
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
