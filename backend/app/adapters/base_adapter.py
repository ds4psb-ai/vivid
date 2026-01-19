"""Base Adapter pattern for capsule execution.

Provides a common interface and shared utilities for all capsule adapters.
Reduces code duplication between GeminiAnalysis, Opal, and Gemini adapters.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AdapterResult:
    """Standardized result from adapter execution."""
    summary: Dict[str, Any]
    evidence_refs: List[str] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0, "total": 0})
    warnings: List[str] = field(default_factory=list)
    
    def merge_token_usage(self, other: Dict[str, int]) -> None:
        """Merge token usage from another source."""
        self.token_usage["input"] += other.get("input", 0)
        self.token_usage["output"] += other.get("output", 0)
        self.token_usage["total"] += other.get("total", 0)


class BaseAdapter(ABC):
    """Abstract base class for capsule adapters.
    
    All concrete adapters (GeminiAnalysis, Opal, Gemini) should inherit from this class
    and implement the `run` method.
    
    Example:
        class GeminiAnalysisAdapter(BaseAdapter):
            def run(self, context: AdapterContext) -> AdapterResult:
                # Implementation
                pass
    """
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"adapter.{name}")
    
    @abstractmethod
    def run(
        self,
        capsule_id: str,
        capsule_version: str,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        capsule_spec: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AdapterResult:
        """Execute the adapter logic.
        
        Args:
            capsule_id: Capsule identifier (e.g., "auteur.bong-joon-ho")
            capsule_version: Version string
            inputs: Input data for generation
            params: Style parameters
            capsule_spec: Optional capsule specification
            **kwargs: Additional adapter-specific arguments
            
        Returns:
            AdapterResult with summary and evidence refs.
        """
        pass
    
    def _extract_pattern_version(self, capsule_spec: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract pattern version from capsule spec (handles both camelCase and snake_case)."""
        if not capsule_spec:
            return None
        return capsule_spec.get("patternVersion") or capsule_spec.get("pattern_version")
    
    def _extract_adapter_config(self, capsule_spec: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract adapter configuration from capsule spec."""
        return (capsule_spec or {}).get("adapter", {})
    
    def _safe_run(
        self,
        capsule_id: str,
        capsule_version: str,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        capsule_spec: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AdapterResult:
        """Run the adapter with error handling.
        
        Wraps the `run` method with try-except and returns a fallback result on error.
        """
        try:
            return self.run(capsule_id, capsule_version, inputs, params, capsule_spec, **kwargs)
        except Exception as exc:
            self.logger.error(f"{self.name} adapter error: {exc}")
            return AdapterResult(
                summary={"summary": f"{self.name} fallback: {exc}", "error": str(exc)},
                evidence_refs=[],
            )


class AdapterChain:
    """Chain of adapters to execute in sequence.
    
    Implements the Chain of Responsibility pattern for executing multiple adapters.
    """
    
    def __init__(self, adapters: Optional[List[BaseAdapter]] = None):
        self.adapters = adapters or []
    
    def add(self, adapter: BaseAdapter) -> "AdapterChain":
        """Add an adapter to the chain."""
        self.adapters.append(adapter)
        return self
    
    def run_all(
        self,
        capsule_id: str,
        capsule_version: str,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        capsule_spec: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Tuple[List[AdapterResult], Dict[str, int]]:
        """Run all adapters in the chain and aggregate results.
        
        Returns:
            Tuple of (list of results, aggregated token usage).
        """
        results = []
        total_usage = {"input": 0, "output": 0, "total": 0}
        
        for adapter in self.adapters:
            result = adapter._safe_run(
                capsule_id, capsule_version, inputs, params, capsule_spec, **kwargs
            )
            results.append(result)
            
            # Aggregate token usage
            total_usage["input"] += result.token_usage.get("input", 0)
            total_usage["output"] += result.token_usage.get("output", 0)
            total_usage["total"] += result.token_usage.get("total", 0)
        
        return results, total_usage


def aggregate_token_usage(*usages: Dict[str, int]) -> Dict[str, int]:
    """Aggregate multiple token usage dictionaries."""
    total = {"input": 0, "output": 0, "total": 0}
    for usage in usages:
        total["input"] += usage.get("input", 0)
        total["output"] += usage.get("output", 0)
        total["total"] += usage.get("total", 0)
    return total
