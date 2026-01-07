"""Constellation Models.

Models for managing multi-scene projects (별자리).
A Constellation connects multiple Singularities (특이점) to create a cohesive story.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Any

from sqlalchemy import String, DateTime, Integer, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Constellation(Base):
    """별자리 - N개 씬 프로젝트 (특이점들을 연결).

    A Constellation is a multi-scene project that connects multiple Singularities
    (BlackholeTemplates) with shared context for consistency across scenes.

    Cosmic Metaphor:
    - 특이점 (Singularity/★): Single best-practice workflow pattern
    - 블랙홀 (Blackhole/🌀): Tag-based collection of singularities (UI filter)
    - 별자리 (Constellation/✨): Multi-scene project connecting singularities
    """
    __tablename__ = "constellations"
    __table_args__ = (
        Index("ix_constellations_creator", "creator_id"),
        Index("ix_constellations_preset", "preset"),
        Index("ix_constellations_is_public", "is_public"),
        Index("ix_constellations_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Project type
    preset: Mapped[str] = mapped_column(String(64), default="short_drama")
    # Presets: "short_drama" (3-5 scenes), "medium" (10-15 scenes), "feature_film" (30+ scenes)

    # Target scene count (user-defined goal)
    target_scene_count: Mapped[int] = mapped_column(Integer, default=5)

    # Shared context across all scenes (for consistency)
    # Structure: {
    #   "characters": {"hero": {"name": "영희", "singularity_ref": "char_001"}, ...},
    #   "visual_style": "singularity_wongkarwai_neon",  # Reference to singularity
    #   "audio_style": "singularity_melancholic_jazz",   # Reference to singularity
    #   "custom_params": {...}  # Additional shared parameters
    # }
    shared_context: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Star points - scenes in the constellation (JSONB embedded, not separate table)
    # Structure: [
    #   {
    #     "scene_number": 1,
    #     "singularity_id": "uuid-string",  # Reference to BlackholeTemplate
    #     "singularity_name": "도시_야경_멜랑콜리",  # Denormalized for display
    #     "status": "pending" | "generating" | "done" | "error",
    #     "thumbnail_url": "...",  # Generated output thumbnail
    #     "overrides": {"mood": "longing", "characters": ["hero"], ...},
    #     "output_ref": "capsule_run_uuid",  # Reference to generated content
    #     "created_at": "ISO timestamp"
    #   },
    #   ...
    # ]
    star_points: Mapped[list] = mapped_column(JSONB, default=list)

    # Creator
    creator_id: Mapped[str] = mapped_column(String(160))
    creator_name: Mapped[str] = mapped_column(String(100), default="Anonymous")

    # Visibility
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Statistics
    use_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def scene_count(self) -> int:
        """Current number of scenes in the constellation."""
        return len(self.star_points) if self.star_points else 0

    @property
    def completed_count(self) -> int:
        """Number of completed scenes."""
        if not self.star_points:
            return 0
        return sum(1 for s in self.star_points if s.get("status") == "done")

    @property
    def progress_percent(self) -> float:
        """Progress percentage (completed / target)."""
        if self.target_scene_count == 0:
            return 0.0
        return round((self.completed_count / self.target_scene_count) * 100, 1)

    def add_star(
        self,
        singularity_id: str,
        singularity_name: str,
        overrides: Optional[dict] = None,
        scene_number: Optional[int] = None
    ) -> dict:
        """Add a new star (scene) to the constellation.

        Args:
            singularity_id: UUID of the BlackholeTemplate to use
            singularity_name: Name of the singularity (denormalized)
            overrides: Scene-specific parameter overrides
            scene_number: Position in sequence (auto-increments if None)

        Returns:
            The created star point dict

        Raises:
            ValueError: If scene_number already exists
        """
        if self.star_points is None:
            self.star_points = []

        # Auto-increment scene number if not specified
        if scene_number is None:
            scene_number = len(self.star_points) + 1
        else:
            # Check for duplicates
            existing_numbers = {s.get("scene_number") for s in self.star_points}
            if scene_number in existing_numbers:
                raise ValueError(f"Scene number {scene_number} already exists")

        star = {
            "scene_number": scene_number,
            "singularity_id": singularity_id,
            "singularity_name": singularity_name,
            "status": "pending",
            "thumbnail_url": None,
            "overrides": overrides or {},
            "output_ref": None,
            "created_at": datetime.utcnow().isoformat()
        }

        self.star_points.append(star)
        return star

    def update_star(self, scene_number: int, updates: dict) -> Optional[dict]:
        """Update a star by scene number.

        Args:
            scene_number: The scene number to update
            updates: Dict of fields to update

        Returns:
            Updated star point or None if not found
        """
        if not self.star_points:
            return None

        for star in self.star_points:
            if star.get("scene_number") == scene_number:
                star.update(updates)
                return star
        return None

    def remove_star(self, scene_number: int) -> bool:
        """Remove a star by scene number.

        Args:
            scene_number: The scene number to remove

        Returns:
            True if removed, False if not found
        """
        if not self.star_points:
            return False

        original_len = len(self.star_points)
        self.star_points = [s for s in self.star_points if s.get("scene_number") != scene_number]

        # Re-number remaining scenes
        for i, star in enumerate(self.star_points):
            star["scene_number"] = i + 1

        return len(self.star_points) < original_len

    def get_star(self, scene_number: int) -> Optional[dict]:
        """Get a star by scene number.

        Args:
            scene_number: The scene number to get

        Returns:
            Star point dict or None if not found
        """
        if not self.star_points:
            return None

        for star in self.star_points:
            if star.get("scene_number") == scene_number:
                return star
        return None
