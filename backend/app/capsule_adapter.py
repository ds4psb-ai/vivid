"""Capsule Adapter: Execute capsule logic and generate style outputs.

This module provides adapters for running capsule nodes. Currently uses
rule-based style generation; future versions will integrate with Gemini/LLM.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

# Color palettes for each auteur style
AUTEUR_PALETTES = {
    "auteur.bong-joon-ho": {
        "cool": ["#102A43", "#243B53", "#334E68", "#486581", "#627D98"],
        "neutral": ["#1F2933", "#323F4B", "#3E4C59", "#52606D", "#7B8794"],
        "warm": ["#27241D", "#423D33", "#504A40", "#625D52", "#857F72"],
    },
    "auteur.park-chan-wook": {
        "cool": ["#1B1B3A", "#2D2D5A", "#462255", "#6B2D5B", "#8B3A62"],
        "neutral": ["#2D132C", "#801336", "#C72C41", "#EE4540", "#F5A962"],
        "warm": ["#3D0C02", "#780116", "#C32F27", "#D8572A", "#F7B538"],
    },
    "auteur.shinkai": {
        "cool": ["#1A365D", "#2C5282", "#3182CE", "#63B3ED", "#90CDF4"],
        "neutral": ["#2D3748", "#4A5568", "#718096", "#A0AEC0", "#CBD5E0"],
        "warm": ["#744210", "#975A16", "#D69E2E", "#ECC94B", "#F6E05E"],
    },
    "auteur.lee-junho": {
        "cool": ["#1A202C", "#2D3748", "#4A5568", "#00B5D8", "#00D9FF"],
        "neutral": ["#171923", "#2D3748", "#4A5568", "#A0AEC0", "#E2E8F0"],
        "warm": ["#1A1423", "#38184C", "#6B21A8", "#9F7AEA", "#E9D8FD"],
    },
    "auteur.na-hongjin": {
        "cool": ["#0D1117", "#161B22", "#21262D", "#30363D", "#484F58"],
        "neutral": ["#1C1C1C", "#2D2D2D", "#3D3D3D", "#4D4D4D", "#5D5D5D"],
        "warm": ["#1A1610", "#2D2418", "#42351F", "#594626", "#70572D"],
    },
    "auteur.hong-sangsoo": {
        "cool": ["#F7FAFC", "#EDF2F7", "#E2E8F0", "#CBD5E0", "#A0AEC0"],
        "neutral": ["#FAFAFA", "#F5F5F5", "#EEEEEE", "#E0E0E0", "#BDBDBD"],
        "warm": ["#FFFBEB", "#FEF3C7", "#FDE68A", "#FCD34D", "#FBBF24"],
    },
}

COMPOSITION_HINTS = {
    "auteur.bong-joon-ho": {
        "static": ["wide establishing", "static master"],
        "controlled": ["symmetry with tension", "vertical blocking", "staircase motif", "class divide framing"],
        "dynamic": ["push-in reveal", "tracking across barrier"],
    },
    "auteur.park-chan-wook": {
        "static": ["centered tableau", "mirror composition"],
        "controlled": ["symmetrical hallway", "split diopter", "wallpaper pattern"],
        "dynamic": ["360 pan", "overhead dolly"],
    },
    "auteur.shinkai": {
        "static": ["wide sky panorama", "silhouette against sunset"],
        "controlled": ["light beam through clouds", "rain reflection", "train window"],
        "dynamic": ["comet trail", "time-lapse clouds"],
    },
    "auteur.lee-junho": {
        "static": ["stage center spotlight"],
        "controlled": ["rythmic cuts", "synced movement"],
        "dynamic": ["whip pan", "jump cut sequence", "beat-matched edit"],
    },
    "auteur.na-hongjin": {
        "static": ["claustrophobic close-up"],
        "controlled": ["over-the-shoulder tension"],
        "dynamic": ["handheld chase", "shaky pursuit", "collision course"],
    },
    "auteur.hong-sangsoo": {
        "static": ["static wide two-shot", "table composition"],
        "controlled": ["slow zoom", "sudden pan to window"],
        "dynamic": ["reframe pan"],
    },
}

PACING_HINTS = {
    "slow": ["long takes > 10s", "contemplative pauses", "minimal cuts", "breathing room"],
    "medium": ["balanced rhythm", "3-5s average shot", "scene-appropriate transitions"],
    "fast": ["rapid cuts < 2s", "impact frames", "jump cuts", "urgency"],
}

ENABLE_EXTERNAL_ADAPTERS = os.getenv("ENABLE_EXTERNAL_ADAPTERS", "false").lower() in (
    "1",
    "true",
    "yes",
)
NOTEBOOKLM_API_URL = os.getenv("NOTEBOOKLM_API_URL", "")
NOTEBOOKLM_API_KEY = os.getenv("NOTEBOOKLM_API_KEY", "")
OPAL_API_URL = os.getenv("OPAL_API_URL", "")
OPAL_API_KEY = os.getenv("OPAL_API_KEY", "")
EXTERNAL_ADAPTER_TIMEOUT = float(os.getenv("EXTERNAL_ADAPTER_TIMEOUT", "15"))
EXTERNAL_ADAPTER_RETRIES = int(os.getenv("EXTERNAL_ADAPTER_RETRIES", "1"))

logger = logging.getLogger(__name__)


def validate_input_contracts(
    inputs: Dict[str, Any],
    input_contracts: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Validate inputs against capsule input contracts.
    
    Args:
        inputs: The actual inputs provided.
        input_contracts: The contract definition from capsule spec.
    
    Returns:
        Tuple of (is_valid, errors).
    """
    errors: List[str] = []
    
    required = input_contracts.get("required", [])
    optional = input_contracts.get("optional", [])
    max_upstream = input_contracts.get("maxUpstream")
    allowed_types = input_contracts.get("allowedTypes", [])
    
    # Check required inputs
    for key in required:
        if key not in inputs or inputs[key] is None:
            errors.append(f"Missing required input: {key}")
    
    # Check unknown inputs (warn only)
    all_known = set(required) | set(optional)
    for key in inputs:
        if key not in all_known and all_known:
            logger.warning("Unknown input key (not in contract): %s", key)
    
    # Check maxUpstream if provided
    if max_upstream is not None:
        upstream_count = len([k for k in inputs if inputs[k] is not None])
        if upstream_count > max_upstream:
            errors.append(f"Too many upstream inputs: {upstream_count} > {max_upstream}")
    
    # Check allowedTypes if provided
    if allowed_types:
        for key, value in inputs.items():
            if value is None:
                continue
            value_type = type(value).__name__
            # Simple type mapping
            type_map = {
                "str": "string",
                "int": "number",
                "float": "number",
                "list": "array",
                "dict": "object",
                "bool": "boolean",
            }
            mapped_type = type_map.get(value_type, value_type)
            if mapped_type not in allowed_types and value_type not in allowed_types:
                # Warning only for type mismatch (not hard error)
                logger.warning("Input %s has type %s, expected one of %s", key, mapped_type, allowed_types)
    
    is_valid = len(errors) == 0
    if errors:
        logger.error("Input contract validation failed: %s", errors)
    
    return is_valid, errors


def _call_external_api(
    url: str,
    api_key: str,
    payload: Dict[str, Any],
    timeout: float,
    retries: int,
) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            logger.info("Adapter call %s attempt=%s", url, attempt + 1)
            request = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read().decode("utf-8")
            return json.loads(data)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning("Adapter call failed %s attempt=%s error=%s", url, attempt + 1, exc)
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    raise last_exc or RuntimeError("Adapter call failed")


def _run_notebooklm(
    capsule_id: str,
    capsule_version: str,
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    capsule_spec: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Run NotebookLM analysis using Gemini-based client.
    
    This function:
    1. Builds a source pack from available segment data
    2. Runs Gemini-based Logic/Persona extraction
    3. Generates variation guide and claims
    """
    from app.config import settings
    
    # Check if Gemini (NotebookLM substitute) is enabled
    if not settings.GEMINI_ENABLED or not settings.GEMINI_API_KEY:
        logger.info("NotebookLM (Gemini) adapter disabled; returning simulated summary")
        return (
            {"summary": "NotebookLM simulated summary", "source_count": 3},
            [],
        )
    
    adapter = (capsule_spec or {}).get("adapter", {})
    pattern_version = (capsule_spec or {}).get("patternVersion") or (
        capsule_spec or {}
    ).get("pattern_version")
    
    # Build a minimal source pack from inputs
    cluster_id = inputs.get("cluster_id") or adapter.get("clusterRef") or f"CL_{capsule_id.split('.')[-1].upper()}"
    temporal_phase = inputs.get("temporal_phase") or "HOOK"
    
    raw_source_ids = inputs.get("source_id") or inputs.get("sourceId") or []
    if isinstance(raw_source_ids, str):
        source_ids = [raw_source_ids.strip()] if raw_source_ids.strip() else []
    elif isinstance(raw_source_ids, list):
        source_ids = [item.strip() for item in raw_source_ids if isinstance(item, str) and item.strip()]
    else:
        source_ids = []
    source_pack = {
        "pack_id": f"sp_{cluster_id}_{temporal_phase}",
        "cluster_id": cluster_id,
        "temporal_phase": temporal_phase,
        "source_count": inputs.get("source_count", 0) or len(source_ids),
        "source_ids": source_ids,
        "segment_refs": inputs.get("segment_refs", []),
        "metrics_snapshot": inputs.get("metrics_snapshot", {}),
        "bundle_hash": inputs.get("bundle_hash", ""),
    }
    
    try:
        from app.narrative_utils import normalize_story_beats, normalize_storyboard_cards
        from app.notebooklm_client import (
            generate_story_beats,
            generate_storyboard_cards,
            run_notebooklm_analysis,
        )
        
        summary, evidence_refs = run_notebooklm_analysis(source_pack, capsule_id)
        if isinstance(summary, dict):
            guide = summary.get("guide", {})
            claims = summary.get("claims", [])
            story_beats = summary.get("story_beats")
            if isinstance(story_beats, list):
                story_beats = normalize_story_beats(story_beats)
                summary["story_beats"] = story_beats
            else:
                story_beats = generate_story_beats(source_pack, capsule_id, guide, claims)
                summary["story_beats"] = story_beats
            storyboard_cards = summary.get("storyboard_cards")
            if isinstance(storyboard_cards, list):
                summary["storyboard_cards"] = normalize_storyboard_cards(storyboard_cards)
            else:
                summary["storyboard_cards"] = generate_storyboard_cards(
                    source_pack,
                    capsule_id,
                    guide,
                    claims,
                    story_beats or [],
                )
        
        # Add pattern version to summary
        if pattern_version:
            summary["pattern_version"] = pattern_version
        
        return summary, evidence_refs
        
    except Exception as exc:
        logger.error(f"NotebookLM adapter error: {exc}")
        return (
            {"summary": f"NotebookLM fallback: {exc}", "error": str(exc)},
            [],
        )




def _run_opal(
    capsule_id: str,
    capsule_version: str,
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    capsule_spec: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    adapter = (capsule_spec or {}).get("adapter", {})
    pattern_version = (capsule_spec or {}).get("patternVersion") or (
        capsule_spec or {}
    ).get("pattern_version")
    payload = {
        "workflow": adapter.get("workflow", "auteur_capsule_v1"),
        "capsule_id": capsule_id,
        "capsule_version": capsule_version,
        "pattern_version": pattern_version,
        "inputs": inputs,
        "params": params,
        "internal_graph_ref": adapter.get("internalGraphRef"),
    }
    if ENABLE_EXTERNAL_ADAPTERS and OPAL_API_URL:
        try:
            response = _call_external_api(
                OPAL_API_URL,
                OPAL_API_KEY,
                payload,
                EXTERNAL_ADAPTER_TIMEOUT,
                EXTERNAL_ADAPTER_RETRIES,
            )
            summary = {
                "summary": response.get("summary") or response.get("output") or "Opal workflow executed",
                "workflow": response.get("workflow", "opal"),
            }
            if response.get("audio_overview") is not None:
                summary["audio_overview"] = response.get("audio_overview")
            if response.get("mind_map") is not None:
                summary["mind_map"] = response.get("mind_map")
            evidence = response.get("evidence_refs", [])
            return summary, evidence
        except Exception as exc:  # noqa: BLE001
            return (
                {"summary": f"Opal fallback: {exc}"},
                [],
            )
    logger.info("Opal adapter disabled or missing URL; returning simulated result")
    return (
        {"summary": "Opal simulated workflow result", "workflow": "mock"},
        [],
    )


def _run_gemini(
    capsule_id: str,
    capsule_version: str,
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    capsule_spec: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Run Gemini adapter for storyboard and shot contract generation."""
    from app.config import settings
    
    if not settings.GEMINI_ENABLED or not settings.GEMINI_API_KEY:
        logger.info("Gemini adapter disabled or missing API key; returning fallback")
        return (
            {"summary": "Gemini disabled, using rule-based generation"},
            [],
        )
    
    try:
        from app.gemini_client import (
            generate_storyboard_with_gemini,
            generate_shot_contracts_with_gemini,
            GeminiGenerationError,
        )
        from app.narrative_utils import normalize_storyboard_cards
        
        # Generate storyboard
        storyboard, storyboard_usage = generate_storyboard_with_gemini(
            inputs, params, capsule_id
        )
        
        # Generate shot contracts
        shot_contracts, shot_usage = generate_shot_contracts_with_gemini(
            inputs, storyboard, params, capsule_id
        )
        
        # Combine token usage
        total_usage = {
            "input": storyboard_usage.get("input", 0) + shot_usage.get("input", 0),
            "output": storyboard_usage.get("output", 0) + shot_usage.get("output", 0),
            "total": storyboard_usage.get("total", 0) + shot_usage.get("total", 0),
        }
        
        summary_storyboard = normalize_storyboard_cards(storyboard)
        summary = {
            "summary": f"Gemini generated {len(storyboard)} storyboard cards, {len(shot_contracts)} shot contracts",
            "storyboard_cards": summary_storyboard,
            "shot_contracts": shot_contracts,
            "token_usage": total_usage,
            "model": settings.GEMINI_MODEL,
        }
        
        return summary, []
        
    except Exception as exc:
        logger.error(f"Gemini adapter error: {exc}")
        return (
            {"summary": f"Gemini fallback: {exc}", "error": str(exc)},
            [],
        )


def _normalize_evidence_refs(
    refs: List[str],
    strict: bool = True,
) -> Tuple[List[str], List[str]]:
    """Normalize and filter evidence refs.
    
    Args:
        refs: List of raw evidence reference strings.
        strict: If True, reject non-compliant refs; if False, map to fallback.
    
    Returns:
        Tuple of (normalized_refs, warnings).
    """
    normalized: List[str] = []
    warnings: List[str] = []
    seen: set[str] = set()
    
    ALLOWED_DB_TABLES = {
        "raw_assets", "video_segments", "evidence_records",
        "patterns", "pattern_trace", "notebook_library",
    }
    
    for ref in refs:
        if not isinstance(ref, str):
            warnings.append(f"Non-string ref ignored: {type(ref)}")
            continue
        cleaned = ref.strip()
        if not cleaned:
            continue
        
        # Already compliant
        if cleaned.startswith("sheet:"):
            mapped = cleaned
        elif cleaned.startswith("db:"):
            # Validate db table is allowed
            parts = cleaned.split(":")
            if len(parts) >= 2 and parts[1] in ALLOWED_DB_TABLES:
                mapped = cleaned
            else:
                table = parts[1] if len(parts) >= 2 else "unknown"
                warnings.append(f"Disallowed db table: {table} in {cleaned}")
                if strict:
                    continue
                mapped = f"sheet:CREBIT_DERIVED_INSIGHTS:{table}_{parts[2] if len(parts) > 2 else 'unknown'}"
        # Legacy format conversion
        elif cleaned.startswith("evidence:sheet:row:"):
            row_id = cleaned.replace("evidence:sheet:row:", "", 1).strip() or "unknown"
            mapped = f"sheet:CREBIT_DERIVED_INSIGHTS:{row_id}"
            warnings.append(f"Legacy ref converted: {cleaned} -> {mapped}")
        # Non-compliant refs
        else:
            warnings.append(f"Non-compliant ref: {cleaned}")
            if strict:
                continue
            safe = "".join(
                ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in cleaned
            )
            mapped = f"sheet:CREBIT_DERIVED_INSIGHTS:{safe or 'unknown'}"
        
        if mapped in seen:
            continue
        seen.add(mapped)
        normalized.append(mapped)
    
    if warnings:
        logger.warning("Evidence ref normalization warnings: %s", warnings)
    
    return normalized, warnings


def compute_style_vector(params: Dict[str, Any], capsule_id: str) -> List[float]:
    """Generate a style embedding vector based on params."""
    style_intensity = params.get("style_intensity", 0.7)
    
    # Base vector from style intensity
    base = [style_intensity, style_intensity * 0.9, style_intensity * 0.85]
    
    # Color warmth
    color_bias = params.get("color_bias", "neutral")
    if color_bias == "warm":
        base.extend([0.8, 0.5, 0.2])
    elif color_bias == "cool":
        base.extend([0.2, 0.5, 0.8])
    else:
        base.extend([0.5, 0.5, 0.5])
    
    # Camera dynamism
    camera = params.get("camera_motion", "controlled")
    if camera == "dynamic":
        base.extend([0.9, 0.8, 0.85])
    elif camera == "static":
        base.extend([0.1, 0.15, 0.2])
    else:
        base.extend([0.5, 0.55, 0.5])
    
    # Signature param influence
    for key in ["tension_bias", "symmetry_bias", "light_diffusion", "music_sync", "chaos_bias", "stillness"]:
        if key in params:
            val = float(params[key])
            base.extend([val, val * 0.9])
    
    # Pad to fixed length
    while len(base) < 16:
        base.append(random.gauss(0.5, 0.1))
    
    return [round(v, 4) for v in base[:16]]


def get_palette(params: Dict[str, Any], capsule_id: str) -> List[str]:
    """Get color palette for the style."""
    color_bias = params.get("color_bias", "neutral")
    palettes = AUTEUR_PALETTES.get(capsule_id, AUTEUR_PALETTES["auteur.bong-joon-ho"])
    return palettes.get(color_bias, palettes["neutral"])


def get_composition_hints(params: Dict[str, Any], capsule_id: str) -> List[str]:
    """Get composition hints based on camera motion."""
    camera = params.get("camera_motion", "controlled")
    hints_by_auteur = COMPOSITION_HINTS.get(capsule_id, COMPOSITION_HINTS["auteur.bong-joon-ho"])
    hints = hints_by_auteur.get(camera, hints_by_auteur["controlled"])
    
    # Add some variation
    if random.random() > 0.5:
        hints = hints + ["rule of thirds"]
    
    return hints[:4]


def get_pacing_hints(params: Dict[str, Any]) -> List[str]:
    """Get pacing hints based on pacing param."""
    pacing = params.get("pacing", "medium")
    return PACING_HINTS.get(pacing, PACING_HINTS["medium"])


def execute_capsule(
    capsule_id: str,
    capsule_version: str,
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    capsule_spec: Optional[Dict[str, Any]] = None,
    progress_cb: Optional[Callable[[str, int], None]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Execute a capsule and return (summary, evidence_refs).
    
    This is the main adapter entry point. Currently uses rule-based logic.
    Future: integrate with Gemini/LLM for more sophisticated generation.
    """
    # Compute outputs based on auteur style
    if progress_cb:
        progress_cb("Computing style signature", 30)
    style_vector = compute_style_vector(params, capsule_id)
    if progress_cb:
        progress_cb("Selecting palette", 45)
    palette = get_palette(params, capsule_id)
    if progress_cb:
        progress_cb("Assembling composition hints", 60)
    composition_hints = get_composition_hints(params, capsule_id)
    if progress_cb:
        progress_cb("Balancing pacing", 70)
    pacing_hints = get_pacing_hints(params)

    output_contracts = (capsule_spec or {}).get("outputContracts") or (
        capsule_spec or {}
    ).get("output_contracts") or {}
    output_types = output_contracts.get("types") if isinstance(output_contracts, dict) else []
    requires_production = isinstance(output_types, list) and any(
        key in output_types
        for key in ("shot_contracts", "prompt_contracts", "prompt_contract_version", "storyboard_refs")
    )
    
    # Extract signature param for summary
    signature_param = None
    signature_value = None
    for key in ["tension_bias", "symmetry_bias", "light_diffusion", "music_sync", "chaos_bias", "stillness"]:
        if key in params:
            signature_param = key
            signature_value = params[key]
            break
    
    pattern_version = (capsule_spec or {}).get("patternVersion") or (
        capsule_spec or {}
    ).get("pattern_version")
    summary = {
        "message": f"Capsule executed: {capsule_id}@{capsule_version}",
        "capsule_id": capsule_id,
        "version": capsule_version,
        "pattern_version": pattern_version,
        "style_vector": style_vector,
        "palette": palette,
        "composition_hints": composition_hints,
        "pacing_hints": pacing_hints,
        "signature": {
            "param": signature_param,
            "value": signature_value,
        } if signature_param else None,
    }

    if requires_production:
        from app import spec_engine

        production_inputs = {
            **inputs,
            **params,
            "palette": palette,
            "composition_hints": composition_hints,
            "pacing_hints": pacing_hints,
        }
        storyboard_cards = spec_engine._generate_storyboard(production_inputs)
        shot_contracts = spec_engine._generate_shot_contracts(production_inputs, storyboard_cards)
        prompt_contracts = spec_engine._generate_prompt_contracts(shot_contracts)
        storyboard_refs = [
            shot.get("shot_id")
            for shot in shot_contracts
            if isinstance(shot, dict) and shot.get("shot_id")
        ]
        summary = {
            **summary,
            "storyboard_cards": storyboard_cards,
            "shot_contracts": shot_contracts,
            "prompt_contracts": prompt_contracts,
            "prompt_contract_version": "v1",
            "storyboard_refs": storyboard_refs,
        }

    evidence_refs = []
    raw_refs = inputs.get("evidence_refs")
    if isinstance(raw_refs, list):
        evidence_refs = [ref for ref in raw_refs if isinstance(ref, str)]

    adapter = (capsule_spec or {}).get("adapter", {})
    adapter_type = adapter.get("type", "rule")
    chain = adapter.get("chain")
    if not chain:
        if adapter_type == "hybrid":
            chain = ["notebooklm", "opal"]
        elif adapter_type == "notebooklm":
            chain = ["notebooklm"]
        elif adapter_type == "opal":
            chain = ["opal"]
        elif adapter_type == "gemini":
            chain = ["gemini"]
        else:
            chain = []

    external_insights = []
    for step in chain:
        if step == "notebooklm":
            if progress_cb:
                progress_cb("NotebookLM analysis", 80)
            insight, refs = _run_notebooklm(capsule_id, capsule_version, inputs, params, capsule_spec)
            external_insights.append({"adapter": "notebooklm", **insight})
            evidence_refs.extend(refs)
        elif step == "opal":
            if progress_cb:
                progress_cb("Opal workflow", 85)
            insight, refs = _run_opal(capsule_id, capsule_version, inputs, params, capsule_spec)
            external_insights.append({"adapter": "opal", **insight})
            evidence_refs.extend(refs)
        elif step == "gemini":
            if progress_cb:
                progress_cb("Gemini generation", 80)
            insight, refs = _run_gemini(capsule_id, capsule_version, inputs, params, capsule_spec)
            external_insights.append({"adapter": "gemini", **insight})
            evidence_refs.extend(refs)
            # Merge Gemini output into main summary if production outputs present
            if "storyboard_cards" in insight:
                summary["storyboard_cards"] = insight["storyboard_cards"]
            if "shot_contracts" in insight:
                summary["shot_contracts"] = insight["shot_contracts"]
            if "token_usage" in insight:
                summary["token_usage"] = insight["token_usage"]

    if external_insights:
        summary["external_insights"] = external_insights

    if progress_cb:
        progress_cb("Finalizing summary", 95)

    # Normalize evidence refs and record warnings
    normalized_refs, evidence_warnings = _normalize_evidence_refs(evidence_refs, strict=True)
    if evidence_warnings:
        summary["evidence_warnings"] = evidence_warnings

    return summary, normalized_refs


def generate_storyboard_preview(
    summary: Dict[str, Any],
    scene_count: int = 3,
) -> List[Dict[str, Any]]:
    """
    Generate a storyboard preview based on capsule output.
    Returns a list of scene descriptors.
    """
    palette = summary.get("palette", ["#333333"])
    composition_hints = summary.get("composition_hints", ["wide shot"])
    pacing_hints = summary.get("pacing_hints", ["medium pacing"])

    def _duration_hint(value: Any, pacing_note: str) -> str:
        if isinstance(value, (int, float)):
            return f"{int(value)}s"
        lowered = str(pacing_note).lower()
        if "fast" in lowered:
            return "1-2s"
        if "medium" in lowered:
            return "3-5s"
        return "5-10s"

    storyboard_cards = summary.get("storyboard_cards")
    scenes: List[Dict[str, Any]] = []
    if isinstance(storyboard_cards, list) and storyboard_cards:
        for idx, card in enumerate(storyboard_cards[:scene_count], start=1):
            if isinstance(card, dict):
                composition = (
                    card.get("composition")
                    or card.get("shot")
                    or card.get("description")
                    or card.get("note")
                )
                composition = (
                    composition
                    if isinstance(composition, str) and composition.strip()
                    else composition_hints[(idx - 1) % len(composition_hints)]
                )
                dominant = card.get("dominant_color") or card.get("color")
                dominant_color = (
                    dominant
                    if isinstance(dominant, str) and dominant.strip()
                    else palette[(idx - 1) % len(palette)]
                )
                accent = card.get("accent_color")
                accent_color = (
                    accent
                    if isinstance(accent, str) and accent.strip()
                    else palette[idx % len(palette)]
                )
                pacing_note = card.get("pacing_note")
                pacing_note = (
                    pacing_note
                    if isinstance(pacing_note, str) and pacing_note.strip()
                    else pacing_hints[(idx - 1) % len(pacing_hints)]
                )
                scenes.append(
                    {
                        "scene_number": idx,
                        "composition": composition,
                        "dominant_color": dominant_color,
                        "accent_color": accent_color,
                        "pacing_note": pacing_note,
                        "duration_hint": _duration_hint(card.get("duration_sec"), pacing_note),
                    }
                )
                continue
            if isinstance(card, str) and card.strip():
                scenes.append(
                    {
                        "scene_number": idx,
                        "composition": card.strip(),
                        "dominant_color": palette[(idx - 1) % len(palette)],
                        "accent_color": palette[idx % len(palette)],
                        "pacing_note": pacing_hints[(idx - 1) % len(pacing_hints)],
                        "duration_hint": _duration_hint(None, pacing_hints[(idx - 1) % len(pacing_hints)]),
                    }
                )
        if scenes:
            return scenes

    for i in range(scene_count):
        pacing_note = pacing_hints[i % len(pacing_hints)]
        scenes.append(
            {
                "scene_number": i + 1,
                "composition": composition_hints[i % len(composition_hints)],
                "dominant_color": palette[i % len(palette)],
                "accent_color": palette[(i + 2) % len(palette)],
                "pacing_note": pacing_note,
                "duration_hint": _duration_hint(None, pacing_note),
            }
        )

    return scenes
