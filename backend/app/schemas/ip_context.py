"""IPContext schema for IP-First workflows.

Defines the standardized IP context payload injected into workflows/capsules.
SSoT: IP-First Coordination Roadmap v2.1.1 (Decision 005).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.models_ip import IPCatalog, IPWorkflowPreset


class IPContext(BaseModel):
    """Standardized IP context payload.

    This schema is injected into workflow/capsule inputs to ensure
    consistent IP metadata and credit context across the stack.
    """

    ip_id: UUID
    slug: str
    auteur_key: Optional[str] = None
    worldbuilding: Dict[str, Any] = Field(default_factory=dict)
    style_refs: List[str] = Field(default_factory=list)
    pattern_version: Optional[str] = None

    # Credit/royalty context
    estimated_credits: int = 0
    owner_royalty_rate: float = 0.0

    model_config = ConfigDict(extra="ignore", frozen=True)

    @classmethod
    def from_ip_catalog(
        cls,
        ip: "IPCatalog",
        preset: Optional["IPWorkflowPreset"] = None,
        owner_royalty_rate: float = 0.3,
    ) -> "IPContext":
        """Build IPContext from IPCatalog (+ optional preset)."""
        return cls(
            ip_id=ip.id,
            slug=ip.slug,
            auteur_key=ip.auteur_key,
            worldbuilding=ip.worldbuilding or {},
            style_refs=ip.tags or [],
            pattern_version=preset.pattern_version if preset else None,
            estimated_credits=preset.estimated_credits if preset else 0,
            owner_royalty_rate=owner_royalty_rate,
        )

    def to_capsule_inputs(self) -> Dict[str, Any]:
        """Serialize to capsule/workflow inputs."""
        return {
            "ip_id": str(self.ip_id),
            "slug": self.slug,
            "auteur_key": self.auteur_key,
            "worldbuilding": self.worldbuilding,
            "style_refs": self.style_refs,
            "pattern_version": self.pattern_version,
        }
