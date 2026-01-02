"""Source Pack Builder utility for capsule adapters.

Standardizes the creation of source packs from various input formats.
Used by NotebookLM and other adapters that need source pack data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SourcePack:
    """Standardized source pack for adapter consumption.
    
    Encapsulates all source-related data needed for NotebookLM-style analysis.
    """
    pack_id: str
    cluster_id: str
    temporal_phase: str = "HOOK"
    source_count: int = 0
    source_ids: List[str] = field(default_factory=list)
    segment_refs: List[Dict[str, Any]] = field(default_factory=list)
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)
    bundle_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "pack_id": self.pack_id,
            "cluster_id": self.cluster_id,
            "temporal_phase": self.temporal_phase,
            "source_count": self.source_count,
            "source_ids": self.source_ids,
            "segment_refs": self.segment_refs,
            "metrics_snapshot": self.metrics_snapshot,
            "bundle_hash": self.bundle_hash,
        }


class SourcePackBuilder:
    """Builder for creating standardized source packs.
    
    Usage:
        source_pack = (
            SourcePackBuilder()
            .with_cluster_id("CL_BONG")
            .with_source_ids(["src1", "src2"])
            .with_inputs(inputs)
            .build()
        )
    """
    
    def __init__(self):
        self._cluster_id: Optional[str] = None
        self._temporal_phase: str = "HOOK"
        self._source_ids: List[str] = []
        self._segment_refs: List[Dict[str, Any]] = []
        self._metrics_snapshot: Dict[str, Any] = {}
        self._bundle_hash: str = ""
        self._source_count: Optional[int] = None
    
    def with_cluster_id(self, cluster_id: str) -> "SourcePackBuilder":
        """Set the cluster ID."""
        self._cluster_id = cluster_id
        return self
    
    def with_temporal_phase(self, phase: str) -> "SourcePackBuilder":
        """Set the temporal phase (HOOK, BUILD, PEAK, RESOLVE)."""
        self._temporal_phase = phase
        return self
    
    def with_source_ids(self, source_ids: List[str]) -> "SourcePackBuilder":
        """Set source IDs directly."""
        self._source_ids = [s.strip() for s in source_ids if isinstance(s, str) and s.strip()]
        return self
    
    def with_inputs(self, inputs: Dict[str, Any]) -> "SourcePackBuilder":
        """Extract source pack data from inputs dictionary.
        
        Handles various input formats for source_id/sourceId.
        """
        # Handle source_id / sourceId
        raw_source_ids = inputs.get("source_id") or inputs.get("sourceId") or []
        if isinstance(raw_source_ids, str):
            self._source_ids = [raw_source_ids.strip()] if raw_source_ids.strip() else []
        elif isinstance(raw_source_ids, list):
            self._source_ids = [
                item.strip() for item in raw_source_ids 
                if isinstance(item, str) and item.strip()
            ]
        
        # Other fields
        self._segment_refs = inputs.get("segment_refs", [])
        self._metrics_snapshot = inputs.get("metrics_snapshot", {})
        self._bundle_hash = inputs.get("bundle_hash", "")
        self._source_count = inputs.get("source_count")
        
        # Temporal phase
        if inputs.get("temporal_phase"):
            self._temporal_phase = inputs["temporal_phase"]
        
        # Cluster ID from inputs
        if inputs.get("cluster_id"):
            self._cluster_id = inputs["cluster_id"]
        
        return self
    
    def with_adapter_config(self, adapter: Dict[str, Any]) -> "SourcePackBuilder":
        """Extract cluster ID from adapter configuration."""
        if adapter.get("clusterRef") and not self._cluster_id:
            self._cluster_id = adapter["clusterRef"]
        return self
    
    def with_capsule_id(self, capsule_id: str) -> "SourcePackBuilder":
        """Generate a default cluster ID from capsule ID if not set."""
        if not self._cluster_id:
            self._cluster_id = f"CL_{capsule_id.split('.')[-1].upper()}"
        return self
    
    def build(self) -> SourcePack:
        """Build the source pack."""
        if not self._cluster_id:
            self._cluster_id = "CL_DEFAULT"
        
        source_count = self._source_count if self._source_count is not None else len(self._source_ids)
        
        return SourcePack(
            pack_id=f"sp_{self._cluster_id}_{self._temporal_phase}",
            cluster_id=self._cluster_id,
            temporal_phase=self._temporal_phase,
            source_count=source_count,
            source_ids=self._source_ids,
            segment_refs=self._segment_refs,
            metrics_snapshot=self._metrics_snapshot,
            bundle_hash=self._bundle_hash,
        )
