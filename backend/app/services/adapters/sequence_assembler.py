"""Sequence Assembler — Multi-Scene Native Format Generator.

Converts per-scene prompts into engine-native multi-scene formats:
- Kling 3.0: Custom Multi-Shot (2-6 scenes, per-shot duration)
- Seedance 2.0: Narrative Branch with @tag references + "Lens switch" cues
- Veo 3.1: Timestamp Prompting ([0-2s] format) + Extend chain markers

Each engine has hard limits:
  Kling 3.0:  max 6 shots, 3-15s total
  Seedance 2.0: 30-100 words per shot, up to 12 references
  Veo 3.1:  4/6/8s per generation, Extend chaining for 30s+
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────
KLING_MAX_SHOTS = 6
KLING_MIN_TOTAL_SEC = 3
KLING_MAX_TOTAL_SEC = 15

VEO_GENERATION_LENGTHS = [4, 6, 8]  # seconds per single generation
VEO_MAX_EXTEND_CHAIN = 8  # max extend operations (= ~64s total)

SEEDANCE_WORDS_PER_SHOT = (30, 100)
SEEDANCE_MAX_REFS = 12

# Shot-type durations (default weights, normalized to total duration)
SHOT_DURATION_WEIGHTS = {
    "opener": 1.2,
    "middle": 1.0,
    "closer": 1.3,
    "any": 1.0,
}


# ─── Kling 3.0 Custom Multi-Shot ─────────────────────────────────────

def assemble_kling_multishot(
    scenes: List[Dict[str, Any]],
    total_duration: float = 10.0,
) -> List[Dict[str, Any]]:
    """Assemble Kling 3.0 Custom Multi-Shot sequences.

    If scenes > 6, splits into multiple Multi-Shot batches.

    Args:
        scenes: List of scene dicts with 'kling_3_0' prompt and 'techniques'.
        total_duration: Target total duration in seconds (3-15).

    Returns:
        List of Multi-Shot batches, each containing shots with duration.
    """
    total_duration = max(KLING_MIN_TOTAL_SEC, min(KLING_MAX_TOTAL_SEC, total_duration))

    # Split into batches of max 6 shots
    batches = []
    for batch_start in range(0, len(scenes), KLING_MAX_SHOTS):
        batch_scenes = scenes[batch_start:batch_start + KLING_MAX_SHOTS]
        shots = _allocate_kling_durations(batch_scenes, total_duration)
        batches.append({
            "batch_index": len(batches),
            "total_duration_sec": sum(s["duration_sec"] for s in shots),
            "shot_count": len(shots),
            "shots": shots,
            "formatted_prompt": _format_kling_multishot(shots),
        })

    return batches


def _allocate_kling_durations(
    scenes: List[Dict[str, Any]],
    total_sec: float,
) -> List[Dict[str, Any]]:
    """Allocate per-shot durations based on multi_shot_hint weights."""
    shots = []
    weights = []

    for i, scene in enumerate(scenes):
        hint = _get_shot_hint(scene, i, len(scenes))
        weight = SHOT_DURATION_WEIGHTS.get(hint, 1.0)
        weights.append(weight)

    total_weight = sum(weights)
    for i, scene in enumerate(scenes):
        duration = round((weights[i] / total_weight) * total_sec, 1)
        duration = max(1.0, duration)  # minimum 1s per shot
        prompt = scene.get("kling_3_0", scene.get("description_en", ""))

        # Build character binding tokens
        characters = _extract_characters(scene)
        char_bindings = ""
        if characters:
            char_bindings = " ".join(
                f"[{c['label']}: {c['description']}]" for c in characters
            )

        shots.append({
            "shot_number": i + 1,
            "duration_sec": duration,
            "prompt": prompt,
            "character_bindings": char_bindings,
            "hint": _get_shot_hint(scene, i, len(scenes)),
        })

    return shots


def _format_kling_multishot(shots: List[Dict[str, Any]]) -> str:
    """Format shots into Kling Custom Multi-Shot text.

    Example output:
        Shot 1 (3.0s): Wide shot, detective walks into dim alley...
        Shot 2 (2.0s): Close-up of his eyes reflecting neon signs...
    """
    lines = []
    for shot in shots:
        bindings = f" {shot['character_bindings']}" if shot["character_bindings"] else ""
        lines.append(
            f"Shot {shot['shot_number']} ({shot['duration_sec']}s):{bindings} "
            f"{shot['prompt']}"
        )
    return "\n".join(lines)


# ─── Seedance 2.0 Narrative Branch ───────────────────────────────────

def assemble_seedance_narrative(
    scenes: List[Dict[str, Any]],
    references: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Assemble Seedance 2.0 Narrative Branch prompt.

    Inserts "Lens switch" / "Cut to" cues between shots and
    binds @tag references for character/style consistency.

    Args:
        scenes: List of scene dicts with 'seedance_2_0' prompt.
        references: Optional dict of tag->description, e.g.
            {"@Character1": "young woman in red coat", "@Style": "noir"}

    Returns:
        Dict with formatted narrative and reference bindings.
    """
    references = references or {}
    ref_header = ""
    if references:
        ref_lines = [f"{tag}: {desc}" for tag, desc in references.items()]
        ref_header = "References: " + " | ".join(ref_lines) + "\n\n"

    narrative_parts = []
    transition_cues = [
        "Lens switch",
        "Cut to",
        "Next shot",
        "Camera shifts to",
        "Transition to",
    ]

    for i, scene in enumerate(scenes):
        prompt = scene.get("seedance_2_0", scene.get("description_en", ""))

        # Inject @tag references into prompt
        prompt = _inject_seedance_refs(prompt, references)

        # Word count enforcement (30-100 words)
        words = prompt.split()
        if len(words) > SEEDANCE_WORDS_PER_SHOT[1]:
            prompt = " ".join(words[:SEEDANCE_WORDS_PER_SHOT[1]])
        elif len(words) < SEEDANCE_WORDS_PER_SHOT[0]:
            # Pad with style/mood context
            techniques = scene.get("techniques", {})
            padding = _generate_seedance_padding(techniques)
            prompt = f"{prompt}. {padding}"

        if i > 0:
            cue = transition_cues[i % len(transition_cues)]
            narrative_parts.append(f"**{cue}**")

        narrative_parts.append(prompt)

    constraints = _build_seedance_constraints(scenes, references)

    return {
        "reference_bindings": references,
        "reference_count": len(references),
        "shot_count": len(scenes),
        "formatted_prompt": ref_header + "\n".join(narrative_parts),
        "constraints": constraints,
    }


def _inject_seedance_refs(prompt: str, references: Dict[str, str]) -> str:
    """Replace character descriptions with @tag references in prompt."""
    for tag, desc in references.items():
        # If description words appear in prompt, prepend @tag
        desc_words = desc.lower().split()
        if len(desc_words) >= 2:
            # Check if key descriptor words appear
            match_count = sum(1 for w in desc_words if w in prompt.lower())
            if match_count >= 2:
                prompt = f"{tag} {prompt}"
                break
    return prompt


def _generate_seedance_padding(techniques: Dict[str, Any]) -> str:
    """Generate padding text from techniques to meet minimum word count."""
    parts = []
    for cat in ["lighting", "color", "composition"]:
        items = techniques.get(cat, [])
        for item in items[:1]:
            text = _technique_to_text(item)
            parts.append(text)
    return ", ".join(parts) if parts else "cinematic atmosphere"


def _build_seedance_constraints(
    scenes: List[Dict[str, Any]],
    references: Dict[str, str],
) -> str:
    """Build constraints footer for Seedance narrative."""
    constraints = ["Maintain consistent character appearance throughout"]
    if references:
        constraints.append(
            f"Lock {len(references)} reference(s) across all shots"
        )
    constraints.append("Smooth transitions between shots, no jump cuts")
    return ". ".join(constraints) + "."


# ─── Veo 3.1 Timestamp Prompting ─────────────────────────────────────

def assemble_veo_timeline(
    scenes: List[Dict[str, Any]],
    generation_length: int = 8,
) -> List[Dict[str, Any]]:
    """Assemble Veo 3.1 Timestamp Prompting sequences.

    Fits scenes into generation windows (4/6/8s) and chains with
    Extend markers for 30s+ long-form content.

    Args:
        scenes: List of scene dicts with 'veo_3_1' prompt.
        generation_length: Target length per generation (4, 6, or 8 seconds).

    Returns:
        List of generation chunks, each with timestamped shots and
        extend_from markers for chaining.
    """
    if generation_length not in VEO_GENERATION_LENGTHS:
        generation_length = 8

    # Calculate how many scenes fit per generation
    scenes_per_gen = max(1, generation_length // 2)  # ~2s per scene minimum
    chunks = []

    for chunk_start in range(0, len(scenes), scenes_per_gen):
        chunk_scenes = scenes[chunk_start:chunk_start + scenes_per_gen]
        chunk_idx = len(chunks)

        # Allocate timestamps within this generation window
        timestamped = _allocate_veo_timestamps(
            chunk_scenes, generation_length
        )

        # Build extend chain metadata
        extend_meta = {}
        if chunk_idx > 0:
            extend_meta["extend_from"] = f"generation_{chunk_idx - 1}"
            extend_meta["continuity_note"] = (
                "Use last frame of previous generation as start frame"
            )

        if chunk_start + scenes_per_gen < len(scenes):
            extend_meta["extend_to"] = f"generation_{chunk_idx + 1}"
            extend_meta["end_frame_hint"] = _get_end_frame_hint(
                chunk_scenes[-1]
            )

        chunks.append({
            "generation_index": chunk_idx,
            "generation_length_sec": generation_length,
            "shots": timestamped,
            "formatted_prompt": _format_veo_timeline(timestamped),
            "extend_chain": extend_meta,
        })

    return chunks


def _allocate_veo_timestamps(
    scenes: List[Dict[str, Any]],
    total_sec: int,
) -> List[Dict[str, Any]]:
    """Allocate timestamp ranges for Veo scenes."""
    n = len(scenes)
    duration_each = total_sec / n
    timestamped = []

    for i, scene in enumerate(scenes):
        start = round(i * duration_each, 1)
        end = round((i + 1) * duration_each, 1)
        prompt = scene.get("veo_3_1", scene.get("description_en", ""))

        timestamped.append({
            "shot_number": i + 1,
            "time_start": start,
            "time_end": end,
            "prompt": prompt,
        })

    return timestamped


def _format_veo_timeline(shots: List[Dict[str, Any]]) -> str:
    """Format shots into Veo Timestamp Prompting text.

    Example output:
        [0-2.7s] Wide establishing shot, camera slowly pushes in...
        [2.7-5.3s] Cut to close-up, subject turns...
        [5.3-8.0s] Over-shoulder shot reveals...
    """
    lines = []
    for shot in shots:
        lines.append(
            f"[{shot['time_start']}-{shot['time_end']}s] {shot['prompt']}"
        )
    return "\n".join(lines)


def _get_end_frame_hint(scene: Dict[str, Any]) -> str:
    """Extract a hint for the last frame to ensure extend continuity."""
    desc = scene.get("description_en", "")
    # Take last sentence as end-frame hint
    sentences = desc.split(".")
    if len(sentences) > 1:
        return sentences[-2].strip() + "."
    return desc[:100] if desc else "Match previous scene ending."


# ─── Shared Helpers ───────────────────────────────────────────────────

def _get_shot_hint(
    scene: Dict[str, Any],
    index: int,
    total: int,
) -> str:
    """Determine shot hint (opener/middle/closer) from techniques or position."""
    techniques = scene.get("techniques", {})
    # Check for explicit multi_shot_hint in any technique
    for cat_items in techniques.values():
        if isinstance(cat_items, list):
            for item in cat_items:
                if isinstance(item, dict):
                    hint = item.get("multi_shot_hint", "")
                    if hint in ("opener", "middle", "closer"):
                        return hint

    # Fallback to positional heuristic
    if index == 0:
        return "opener"
    elif index == total - 1:
        return "closer"
    return "middle"


def _extract_characters(scene: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract character descriptions for Kling binding tokens."""
    characters = scene.get("characters", [])
    if not characters:
        return []
    result = []
    for i, char in enumerate(characters):
        if isinstance(char, str):
            result.append({"label": f"Character {chr(65 + i)}", "description": char})
        elif isinstance(char, dict):
            label = char.get("name", f"Character {chr(65 + i)}")
            desc = char.get("description", char.get("appearance", ""))
            result.append({"label": label, "description": desc})
    return result


def _technique_to_text(technique) -> str:
    """Convert a technique (str or dict) to English text."""
    if isinstance(technique, str):
        return technique.replace("_", " ")
    if isinstance(technique, dict):
        return technique.get(
            "name_en", technique.get("technique_id", "")
        ).replace("_", " ")
    return str(technique)
