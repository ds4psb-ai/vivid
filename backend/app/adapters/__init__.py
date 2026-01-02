"""Adapter package for capsule execution.

This package provides standardized adapters for different AI services:
- NotebookLM: Logic/Persona extraction with evidence refs
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
from app.adapters.notebooklm_adapter import NotebookLMAdapter
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
    "NotebookLMAdapter",
    "OpalAdapter",
    "GeminiAdapter",
]
