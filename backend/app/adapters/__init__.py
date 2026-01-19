"""Adapter package for capsule execution.

This package provides standardized adapters for different AI services:
- GeminiAnalysis: NotebookLM-style logic/persona extraction (Gemini backend)
- Opal: Workflow orchestration
- Gemini: Direct LLM generation

All adapters follow the BaseAdapter pattern for consistency.
"""
from app.adapters.base_adapter import (
    AdapterResult,
    BaseAdapter,
    AdapterChain,
    aggregate_token_usage,
)
from app.adapters.source_pack_builder import (
    SourcePack,
    SourcePackBuilder,
)
from app.adapters.gemini_analysis_adapter import GeminiAnalysisAdapter
from app.adapters.opal_adapter import OpalAdapter
from app.adapters.gemini_adapter import GeminiAdapter

__all__ = [
    # Base
    "AdapterResult",
    "BaseAdapter",
    "AdapterChain",
    "aggregate_token_usage",
    # Builders
    "SourcePack",
    "SourcePackBuilder",
    # Concrete adapters
    "GeminiAnalysisAdapter",
    "OpalAdapter",
    "GeminiAdapter",
]
