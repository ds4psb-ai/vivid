"""Ideal Persona loader and prompt builder.

Loads rich auteur persona data from JSON files in data/ideal/ directory
and builds context prompts for NotebookLM analysis enhancement.

Usage:
    from app.ideal_persona import load_ideal_persona, build_persona_context
    
    persona = load_ideal_persona("bong-joon-ho")
    context = build_persona_context("auteur.bong-joon-ho")
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

# Path to ideal persona data files
IDEAL_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "ideal"

# Mapping from auteur identifier to filename prefix
# Handles cases where capsule_id differs from ideal data filename
AUTEUR_FILE_MAPPING = {
    "bong-joon-ho": "bong",
    "park-chan-wook": "park",
    "shinkai": "shinkai",
    "lee-junho": "lee",
    "na-hongjin": "na",
    "hong-sangsoo": "hong",
}


def _get_file_prefix(auteur: str) -> str:
    """Get file prefix for an auteur, handling naming variations."""
    clean = auteur.replace("auteur.", "").strip()
    return AUTEUR_FILE_MAPPING.get(clean, clean)


@lru_cache(maxsize=16)
def load_ideal_persona(auteur: str) -> Optional[Dict[str, Any]]:
    """Load ideal persona data for an auteur.
    
    Args:
        auteur: Auteur identifier (e.g., "bong-joon-ho", "park-chan-wook")
        
    Returns:
        Parsed JSON data or None if not found.
    """
    # Use mapping to resolve correct filename prefix
    prefix = _get_file_prefix(auteur)
    
    filename = f"{prefix}_ideal_persona.json"
    filepath = IDEAL_DATA_DIR / filename
    
    if not filepath.exists():
        return None
        
    try:
        with filepath.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


@lru_cache(maxsize=16)
def load_ideal_homage_guide(auteur: str) -> Optional[Dict[str, Any]]:
    """Load ideal homage guide data for an auteur.
    
    Args:
        auteur: Auteur identifier
        
    Returns:
        Parsed JSON data or None if not found.
    """
    # Use mapping to resolve correct filename prefix
    prefix = _get_file_prefix(auteur)
    
    filename = f"{prefix}_ideal_homage_guide.json"
    filepath = IDEAL_DATA_DIR / filename
    
    if not filepath.exists():
        return None
        
    try:
        with filepath.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_thematic_weights(auteur: str) -> Dict[str, float]:
    """Get thematic obsession weights for an auteur.
    
    Args:
        auteur: Auteur identifier
        
    Returns:
        Dict mapping theme names to weights (0.0-1.0).
    """
    persona = load_ideal_persona(auteur)
    if not persona:
        return {}
    
    obsessions = persona.get("thematic_obsessions", [])
    if not isinstance(obsessions, list):
        return {}
    
    return {
        item["theme"]: item.get("weight", 0.5)
        for item in obsessions
        if isinstance(item, dict) and "theme" in item
    }


def get_signature_techniques(auteur: str) -> Dict[str, List[str]]:
    """Get signature techniques for an auteur.
    
    Args:
        auteur: Auteur identifier
        
    Returns:
        Dict with 'visual', 'narrative', 'production' technique lists.
    """
    persona = load_ideal_persona(auteur)
    if not persona:
        return {}
    
    techniques = persona.get("signature_techniques", {})
    if not isinstance(techniques, dict):
        return {}
    
    result = {}
    for category in ("visual", "narrative", "production"):
        items = techniques.get(category, [])
        if isinstance(items, list):
            result[category] = [
                item.get("name", "") if isinstance(item, dict) else str(item)
                for item in items
            ]
    
    return result


def build_persona_context(auteur: str, max_length: int = 800) -> str:
    """Build rich persona context for prompt injection.
    
    Args:
        auteur: Auteur identifier (e.g., "auteur.bong-joon-ho")
        max_length: Maximum context length in characters
        
    Returns:
        Formatted context string for prompt injection.
    """
    persona = load_ideal_persona(auteur)
    if not persona:
        return ""
    
    parts: List[str] = []
    
    # Core philosophy
    philosophy = persona.get("artistic_philosophy", {})
    if isinstance(philosophy, dict):
        core = philosophy.get("core_statement")
        if core:
            parts.append(f"Core Philosophy: {core}")
        
        beliefs = philosophy.get("key_beliefs", [])
        if beliefs and isinstance(beliefs, list):
            beliefs_str = "; ".join(str(b) for b in beliefs[:3])
            parts.append(f"Key Beliefs: {beliefs_str}")
    
    # Thematic obsessions (top 3 by weight)
    obsessions = persona.get("thematic_obsessions", [])
    if isinstance(obsessions, list) and obsessions:
        sorted_themes = sorted(
            obsessions,
            key=lambda x: x.get("weight", 0) if isinstance(x, dict) else 0,
            reverse=True
        )[:3]
        theme_strs = [
            f"{t['theme']} ({t.get('weight', 0):.0%})"
            for t in sorted_themes
            if isinstance(t, dict) and "theme" in t
        ]
        if theme_strs:
            parts.append(f"Thematic Obsessions: {', '.join(theme_strs)}")
    
    # Signature techniques (visual + narrative)
    techniques = get_signature_techniques(auteur)
    if techniques:
        visual = techniques.get("visual", [])[:3]
        narrative = techniques.get("narrative", [])[:3]
        if visual:
            parts.append(f"Visual Signatures: {', '.join(visual)}")
        if narrative:
            parts.append(f"Narrative Signatures: {', '.join(narrative)}")
    
    # Application guide essence
    app_guide = persona.get("application_guide", {})
    if isinstance(app_guide, dict):
        essence = app_guide.get("essence_summary")
        if essence:
            parts.append(f"Essence: {essence}")
    
    context = "\n".join(parts)
    
    # Truncate if too long
    if len(context) > max_length:
        context = context[:max_length-3] + "..."
    
    return context


def build_visual_context(auteur: str, max_length: int = 600) -> str:
    """Build visual language context from homage guide.
    
    Args:
        auteur: Auteur identifier
        max_length: Maximum context length
        
    Returns:
        Formatted visual context string.
    """
    guide = load_ideal_homage_guide(auteur)
    if not guide:
        return ""
    
    parts: List[str] = []
    
    # Blocking
    blocking = guide.get("visual_language", {}).get("blocking", {})
    if isinstance(blocking, dict):
        primary = blocking.get("primary")
        signature = blocking.get("signature")
        if primary:
            parts.append(f"Blocking: {primary}")
        if signature:
            parts.append(f"Signature: {signature[:100]}")
    
    # Camera motion
    camera = guide.get("camera_motion", {})
    if isinstance(camera, dict):
        style = camera.get("primary_style")
        if style:
            parts.append(f"Camera Style: {style}")
        
        movements = camera.get("signature_movements", [])
        if movements and isinstance(movements, list):
            move_names = [
                m.get("name", "") for m in movements[:3]
                if isinstance(m, dict)
            ]
            if move_names:
                parts.append(f"Movements: {', '.join(move_names)}")
    
    # Color palette
    palette = guide.get("color_palette", {})
    if isinstance(palette, dict):
        mood = palette.get("primary_mood")
        if mood:
            parts.append(f"Color Mood: {mood}")
    
    context = " | ".join(parts)
    
    if len(context) > max_length:
        context = context[:max_length-3] + "..."
    
    return context


def get_all_available_auteurs() -> List[str]:
    """Get list of auteurs with ideal persona data.
    
    Returns:
        List of auteur identifiers.
    """
    if not IDEAL_DATA_DIR.exists():
        return []
    
    auteurs = []
    for filepath in IDEAL_DATA_DIR.glob("*_ideal_persona.json"):
        # Extract auteur name from filename
        name = filepath.stem.replace("_ideal_persona", "")
        if name:
            auteurs.append(name)
    
    return sorted(auteurs)
