"""Workflow Tool Registry with Decorator-Based Registration (Phase 2-3).

2026 Best Practices Applied:
- Frozen dataclass with slots for immutability and memory efficiency
- Double-checked locking pattern for lazy initialization (2x performance)
- functools.wraps to preserve function metadata
- Tuple instead of list for immutable tags

Usage:
    @workflow_tool(
        tool_id="prompt_generator",
        capsule_id=DimensionCapsuleId.PROMPT_GENERATE,
        tool_key="generate_veo_prompt",
        display_name="Prompt Generator",
    )
    def build_prompt_inputs(node_inputs: Dict, session: WorkflowSession) -> Dict:
        return {...}

    spec = get_tool_spec("prompt_generator")
"""
from __future__ import annotations

import functools
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from app.dimension_adapter import DimensionCapsuleId
from app.logging_config import get_logger

if TYPE_CHECKING:
    from app.schemas.workflow_session import WorkflowSession

logger = get_logger("workflow_tool_registry")


@dataclass(frozen=True, slots=True)
class WorkflowToolSpec:
    """Workflow tool specification (immutable config).

    Frozen dataclass provides:
    - Immutability: prevents accidental modification
    - Hashability: can be used as dict key
    - Thread-safety: no mutable state

    slots=True provides:
    - ~20% memory reduction per instance
    - Slightly faster attribute access
    """

    tool_id: str
    capsule_id: DimensionCapsuleId
    tool_key: str
    display_name: str
    default_model: str = "gemini-3-flash-preview"
    credit_cost: int = 10
    # Exclude from hash/compare since functions aren't hashable
    input_adapter: Optional[Callable[..., Dict[str, Any]]] = field(
        default=None, hash=False, compare=False
    )
    # Tuple for immutability (list would violate frozen)
    tags: Tuple[str, ...] = field(default_factory=tuple)


# Global registry (module-level singleton)
_tool_registry: Dict[str, WorkflowToolSpec] = {}
_initialized: bool = False
_init_lock = threading.Lock()


def workflow_tool(
    tool_id: str,
    capsule_id: DimensionCapsuleId,
    tool_key: str,
    display_name: str,
    default_model: str = "gemini-3-flash-preview",
    credit_cost: int = 10,
    aliases: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> Callable[[Callable[..., Dict[str, Any]]], Callable[..., Dict[str, Any]]]:
    """Decorator to register a workflow tool with its input adapter.

    Args:
        tool_id: Unique identifier for the tool
        capsule_id: DimensionCapsuleId enum value
        tool_key: Key for capsule execution
        display_name: Human-readable name
        default_model: Default model to use (default: gemini-3-flash-preview)
        credit_cost: Credit cost per execution (default: 10)
        aliases: Optional list of alternative tool IDs (for backwards compatibility)
        tags: Optional list of tags for categorization

    Returns:
        Decorator function that registers the tool and returns the original function
    """

    def decorator(
        func: Callable[..., Dict[str, Any]]
    ) -> Callable[..., Dict[str, Any]]:
        spec = WorkflowToolSpec(
            tool_id=tool_id,
            capsule_id=capsule_id,
            tool_key=tool_key,
            display_name=display_name,
            default_model=default_model,
            credit_cost=credit_cost,
            input_adapter=func,
            tags=tuple(tags) if tags else (),
        )

        _tool_registry[tool_id] = spec
        logger.debug(f"Registered workflow tool: {tool_id}")

        # Register aliases for backwards compatibility
        for alias in aliases or []:
            _tool_registry[alias] = spec
            logger.debug(f"Registered alias: {alias} -> {tool_id}")

        # Preserve function metadata
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _ensure_initialized() -> None:
    """Lazy initialization using double-checked locking pattern.

    Double-checked locking:
    1. First check without lock (fast path for already initialized)
    2. Acquire lock only if needed
    3. Second check inside lock (thread-safety)

    This provides ~2x performance improvement over always locking.
    """
    global _initialized
    if _initialized:  # Fast path
        return
    with _init_lock:
        if not _initialized:  # Double-check inside lock
            # Import adapters to trigger @workflow_tool decorators
            from app.services import workflow_adapters  # noqa: F401

            _initialized = True
            logger.info(f"Workflow tool registry initialized: {len(_tool_registry)} tools")


def get_tool_spec(tool_id: str) -> Optional[WorkflowToolSpec]:
    """Get tool specification by ID.

    Args:
        tool_id: Tool identifier or alias

    Returns:
        WorkflowToolSpec if found, None otherwise
    """
    _ensure_initialized()
    return _tool_registry.get(tool_id)


def get_all_tools() -> Dict[str, WorkflowToolSpec]:
    """Get all registered tools (copy to prevent mutation).

    Returns:
        Dict mapping tool_id to WorkflowToolSpec
    """
    _ensure_initialized()
    return _tool_registry.copy()


def get_credit_cost(tool_id: str) -> int:
    """Get credit cost for a tool.

    Args:
        tool_id: Tool identifier

    Returns:
        Credit cost if found, 0 otherwise
    """
    spec = get_tool_spec(tool_id)
    return spec.credit_cost if spec else 0


def list_tool_ids() -> List[str]:
    """Get list of all registered tool IDs.

    Returns:
        List of tool IDs (excluding aliases)
    """
    _ensure_initialized()
    seen_specs = set()
    unique_ids = []
    for tool_id, spec in _tool_registry.items():
        if id(spec) not in seen_specs:
            seen_specs.add(id(spec))
            unique_ids.append(tool_id)
    return unique_ids


def get_tools_by_tag(tag: str) -> List[WorkflowToolSpec]:
    """Get all tools with a specific tag.

    Args:
        tag: Tag to filter by

    Returns:
        List of matching WorkflowToolSpec
    """
    _ensure_initialized()
    seen_specs = set()
    result = []
    for spec in _tool_registry.values():
        if tag in spec.tags and id(spec) not in seen_specs:
            seen_specs.add(id(spec))
            result.append(spec)
    return result
