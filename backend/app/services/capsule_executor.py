"""Capsule Executor Pipeline.

P5 Commit 2: Unified execution pipeline for all capsule types.
H3.1: OpenLLMetry integration with GenAI semantic conventions.

Adapter Routing:
- teaching.*, dimension.*, veo.* → execute_dimension_capsule
- auteur.* → Tier0 NotebookLM RAG (query_auteur_dna)

Usage:
    from app.services.capsule_executor import execute_capsule

    result = await execute_capsule(
        capsule_id="teaching.prompt.generate:1.0.0",
        inputs={"topic": "테스트"},
        params={"model": "gemini-3-flash-preview"},
        user=current_user,
        db=db,
    )
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# H3.1: OpenLLMetry Tracing Setup
# =============================================================================

def _get_tracer():
    """Get OpenTelemetry tracer for capsule operations."""
    try:
        from opentelemetry import trace
        return trace.get_tracer("vivid.capsule", "1.0.0")
    except ImportError:
        return None


def _get_workflow_decorator():
    """Get traceloop workflow decorator if available."""
    try:
        from traceloop.sdk.decorators import workflow
        return workflow
    except ImportError:
        # Return a no-op decorator if traceloop is not installed
        def noop_decorator(name: str = None):
            def wrapper(func):
                return func
            return wrapper
        return noop_decorator


def _get_task_decorator():
    """Get traceloop task decorator if available."""
    try:
        from traceloop.sdk.decorators import task
        return task
    except ImportError:
        def noop_decorator(name: str = None):
            def wrapper(func):
                return func
            return wrapper
        return noop_decorator


# =============================================================================
# Result Schema (frontend-compatible)
# =============================================================================

@dataclass
class CapsuleExecutionResult:
    """Capsule execution result matching frontend CapsuleRun expectations."""
    run_id: str
    status: str  # done | failed | cancelled
    summary: Dict[str, Any] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)  # P1: string[] for frontend
    version: str = ""
    token_usage: Dict[str, int] = field(default_factory=dict)
    latency_ms: int = 0
    cost_usd_est: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "summary": self.summary,
            "evidence_refs": self.evidence_refs,
            "version": self.version,
            "token_usage": self.token_usage,
            "latency_ms": self.latency_ms,
            "cost_usd_est": self.cost_usd_est,
            "error": self.error,
        }


# =============================================================================
# Input Validation
# =============================================================================

def _validate_inputs(
    inputs: Dict[str, Any],
    spec: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate and merge defaults into inputs.
    
    Args:
        inputs: User-provided inputs
        spec: Capsule spec containing input definitions
    
    Returns:
        Merged inputs with defaults applied
    
    Raises:
        ValueError: If required inputs are missing
    """
    input_defs = spec.get("inputs", {})
    merged = dict(inputs)
    
    for key, definition in input_defs.items():
        is_required = definition.get("required", False)
        default = definition.get("default")
        
        if key not in merged:
            if is_required:
                raise ValueError(f"Missing required input: {key}")
            if default is not None:
                merged[key] = default
    
    return merged


# =============================================================================
# Adapter Selection
# =============================================================================

def _get_adapter_type(capsule_key: str) -> str:
    """Determine adapter type based on capsule_key prefix.
    
    Args:
        capsule_key: e.g., "teaching.prompt.generate", "auteur.bong-joon-ho"
    
    Returns:
        Adapter type: "dimension" or "notebooklm"
    """
    if capsule_key.startswith("auteur.") or capsule_key.startswith("production."):
        return "notebooklm"
    
    # teaching.*, dimension.*, veo.* → dimension adapter
    return "dimension"


# =============================================================================
# Dimension Adapter Execution
# =============================================================================

async def _execute_dimension(
    capsule_key: str,
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute via dimension_adapter (teaching, dimension, veo capsules).
    
    This wraps execute_dimension_capsule from dimension_adapter.py.
    """
    try:
        from app.dimension_adapter import execute_dimension_capsule
        
        result = await execute_dimension_capsule(
            capsule_id=capsule_key,
            inputs=inputs,
            params=params,
            user_api_key=user_api_key,
        )
        return result
    except ImportError as e:
        logger.error(f"Failed to import dimension_adapter: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# NotebookLM Tier0 Execution
# =============================================================================

async def _execute_notebooklm(
    capsule_key: str,
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute via NotebookLM Tier0 RAG (auteur capsules).
    
    P5: All auteur.* capsules use Tier0 NotebookLM RAG regardless of spec.adapter.type.
    This is an intentional override for simplicity in this iteration.
    """
    try:
        from app.rag.tier0_notebooklm import query_auteur_dna
        
        # Extract auteur key from capsule_key (e.g., "auteur.bong-joon-ho" -> "bong")
        auteur_full = capsule_key.replace("auteur.", "").replace("production.", "")
        
        # Map full name to short key
        AUTEUR_KEY_MAP = {
            "bong-joon-ho": "bong",
            "park-chan-wook": "park",
            "shinkai": "shinkai",
            "lee-junho": "lee",
            "na-hongjin": "na",
            "hong-sangsoo": "hong",
            "tarantino": "tarantino",
            "nolan": "nolan",
            "wong": "wong",
        }
        auteur_key = AUTEUR_KEY_MAP.get(auteur_full, auteur_full)
        
        # Build query from inputs
        scene_summary = inputs.get("scene_summary", "")
        emotion_curve = inputs.get("emotion_curve", [])
        query = f"{scene_summary} 감정곡선: {emotion_curve}"
        
        # Query NotebookLM
        result = await query_auteur_dna(auteur_key, query)
        
        if result.confidence > 0.3:
            return {
                "success": True,
                "output": {
                    "answer": result.answer,
                    "confidence": result.confidence,
                    "grounded": result.grounded,
                    "sources": [s.source_id for s in result.sources] if result.sources else [],
                },
                "metrics": {
                    "tokens": 0,  # NotebookLM doesn't report tokens
                },
            }
        else:
            # Low confidence - return simulation
            return {
                "success": True,
                "output": {
                    "answer": f"시뮬레이션 응답: {auteur_key} 스타일 분석",
                    "confidence": 0.5,
                    "grounded": False,
                    "sources": [],
                    "_simulation": True,
                },
                "metrics": {"tokens": 0},
            }
    except ImportError as e:
        logger.warning(f"NotebookLM adapter not available: {e}")
        return {
            "success": True,
            "output": {
                "answer": f"NotebookLM 미설치 - 시뮬레이션 응답",
                "confidence": 0.3,
                "grounded": False,
                "_simulation": True,
            },
            "metrics": {"tokens": 0},
        }
    except Exception as e:
        logger.error(f"NotebookLM execution failed: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# Output Normalization
# =============================================================================

def _normalize_output(
    raw_result: Dict[str, Any],
    capsule_key: str,
) -> Dict[str, Any]:
    """Normalize output to summary, evidence_refs, token_usage only.
    
    This is the "capsule sealing" policy - hide internal details.
    """
    output = raw_result.get("output", {})
    metrics = raw_result.get("metrics", {})
    
    # Extract summary
    summary = {}
    if isinstance(output, dict):
        # Common summary fields
        for key in ["answer", "prompt", "scenes", "analysis", "visual_guidelines", "music_prompt"]:
            if key in output:
                summary[key] = output[key]
        
        # If no known keys, use entire output
        if not summary:
            summary = output
    else:
        summary = {"result": output}
    
    # Extract evidence refs as string[] (P1: simple source_id list)
    evidence_refs: List[str] = []
    if isinstance(output, dict):
        sources = output.get("sources", [])
        if isinstance(sources, list):
            for s in sources:
                if isinstance(s, str):
                    evidence_refs.append(s)
                elif isinstance(s, dict) and "source_id" in s:
                    evidence_refs.append(s["source_id"])
    
    # Extract token usage
    token_usage = {}
    if metrics:
        token_usage = {
            "input": metrics.get("input_tokens", 0),
            "output": metrics.get("output_tokens", 0),
            "total": metrics.get("tokens", 0),
        }
    
    return {
        "summary": summary,
        "evidence_refs": evidence_refs,
        "token_usage": token_usage,
    }


# =============================================================================
# Main Execution Function
# =============================================================================

async def execute_capsule(
    capsule_id: str,
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user: Dict[str, Any],
    db: AsyncSession,
    byok_key: Optional[str] = None,
    run_id: Optional[str] = None,
) -> CapsuleExecutionResult:
    """Execute a capsule with unified pipeline.

    H3.1: Full tracing with OpenLLMetry GenAI semantic conventions.

    Args:
        capsule_id: Format "capsule_key" or "capsule_key:version"
        inputs: User-provided inputs
        params: Execution parameters (model, etc.)
        user: Authenticated user dict
        db: Database session
        byok_key: Optional BYOK API key
        run_id: Optional pre-generated run_id

    Returns:
        CapsuleExecutionResult with normalized output
    """
    import uuid
    from app.services.capsule_specs import parse_capsule_id, get_spec

    start_time = time.monotonic()

    # H3.1: Initialize tracing
    tracer = _get_tracer()
    span = None

    if tracer:
        # Start a span for the capsule execution
        span = tracer.start_span(
            "capsule.execute",
            attributes={
                "vivid.capsule_id": capsule_id,
                "vivid.user_id": user.get("user_id") or user.get("id", "unknown"),
                "gen_ai.system": "google_genai",
                "gen_ai.request.model": params.get("model", "gemini-3-flash-preview") if params else "gemini-3-flash-preview",
            }
        )
    
    # Normalize params to avoid None cases
    params = dict(params) if params else {}

    # Generate run_id if not provided
    if not run_id:
        run_id = str(uuid.uuid4())
    
    # Parse capsule_id
    capsule_key, version = parse_capsule_id(capsule_id)
    
    # Get spec for validation
    try:
        spec_response = await get_spec(db, capsule_key, version)
        if not spec_response:
            return CapsuleExecutionResult(
                run_id=run_id,
                status="failed",
                error=f"Capsule not found: {capsule_id}",
                version=version or "unknown",
            )
        spec = spec_response.spec
        version = spec_response.version
    except Exception as e:
        logger.warning(f"Spec lookup failed, proceeding without validation: {e}")
        spec = {}
        version = version or "1.0.0"
    
    # Validate and merge inputs
    try:
        validated_inputs = _validate_inputs(inputs, spec)
    except ValueError as e:
        return CapsuleExecutionResult(
            run_id=run_id,
            status="failed",
            error=str(e),
            version=version,
        )

    # -------------------------------------------------------------------------
    # Phase 7: Generation A/B Testing (optional)
    # -------------------------------------------------------------------------
    ab_result = None
    try:
        experiment_key = params.get("ab_experiment_key") or params.get("ab_experiment_id")
        user_id = user.get("user_id") or user.get("id")
        if experiment_key and user_id:
            from app.experiments import get_ab_testing
            from app.experiments.generation_ab import GenerationABService

            ab_service = get_ab_testing()
            gen_ab = GenerationABService(ab_service)
            ab_result = await gen_ab.get_variant_config(
                experiment_key=experiment_key,
                user_id=str(user_id),
                db=db,
                base_params=params,
                base_inputs=validated_inputs,
                context={
                    "capsule_id": capsule_id,
                    "capsule_key": capsule_key,
                    "version": version,
                },
            )
            if ab_result:
                validated_inputs = ab_result.inputs
                params = ab_result.params
                logger.info(
                    "[A/B] Assigned variant %s for %s",
                    ab_result.variant_name,
                    experiment_key,
                )
    except Exception as e:
        logger.warning(f"[A/B] Variant assignment skipped: {e}")

    # Determine adapter
    adapter_type = _get_adapter_type(capsule_key)
    
    # Execute
    try:
        if adapter_type == "dimension":
            raw_result = await _execute_dimension(
                capsule_key=capsule_key,
                inputs=validated_inputs,
                params=params,
                user_api_key=byok_key,
            )
        else:  # notebooklm
            raw_result = await _execute_notebooklm(
                capsule_key=capsule_key,
                inputs=validated_inputs,
                params=params,
                user_api_key=byok_key,
            )
    except Exception as e:
        logger.error(f"Capsule execution failed: {e}")
        raw_result = {"success": False, "error": str(e)}
    
    latency_ms = int((time.monotonic() - start_time) * 1000)
    
    # Determine status
    if raw_result.get("success"):
        status = "done"
        error = None
    else:
        status = "failed"
        error = raw_result.get("error", "Unknown error")
    
    # Normalize output
    normalized = _normalize_output(raw_result, capsule_key)

    # Attach A/B experiment metadata (if assigned)
    if ab_result:
        normalized["summary"]["ab_experiment"] = {
            "experiment_key": ab_result.experiment_key,
            "variant_name": ab_result.variant_name,
            "is_control": ab_result.is_control,
        }
    
    # Estimate cost (simplified)
    tokens = normalized["token_usage"].get("total", 0)
    cost_usd_est = tokens * 0.00001  # ~$10/1M tokens estimate
    
    result = CapsuleExecutionResult(
        run_id=run_id,
        status=status,
        summary=normalized["summary"],
        evidence_refs=normalized["evidence_refs"],
        version=version,
        token_usage=normalized["token_usage"],
        latency_ms=latency_ms,
        cost_usd_est=cost_usd_est,
        error=error,
    )

    # H3.1: Record trace attributes and metrics
    if span:
        try:
            from opentelemetry.trace import StatusCode

            # Set GenAI semantic convention attributes
            span.set_attribute("gen_ai.usage.input_tokens", normalized["token_usage"].get("input", 0))
            span.set_attribute("gen_ai.usage.output_tokens", normalized["token_usage"].get("output", 0))
            span.set_attribute("gen_ai.usage.total_tokens", normalized["token_usage"].get("total", 0))
            span.set_attribute("vivid.capsule_key", capsule_key)
            span.set_attribute("vivid.version", version)
            span.set_attribute("vivid.latency_ms", latency_ms)
            span.set_attribute("vivid.cost_usd_est", cost_usd_est)

            if status == "done":
                span.set_status(StatusCode.OK)
            else:
                span.set_status(StatusCode.ERROR, error or "Unknown error")

            span.end()
        except Exception as e:
            logger.warning(f"Failed to record span attributes: {e}")

    # H3.1: Record Prometheus metrics
    try:
        from app.telemetry import record_llm_request

        dimension = capsule_key.split(".")[0] if "." in capsule_key else capsule_key
        model = params.get("model", "gemini-3-flash-preview") if params else "gemini-3-flash-preview"

        record_llm_request(
            model=model,
            dimension=dimension,
            status="success" if status == "done" else "failed",
            input_tokens=normalized["token_usage"].get("input", 0),
            output_tokens=normalized["token_usage"].get("output", 0),
            latency_seconds=latency_ms / 1000.0,
            credits=cost_usd_est * 100,  # Convert USD to credits estimate
            error_type=error[:50] if error else None,
        )
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to record LLM metrics: {e}")

    return result
