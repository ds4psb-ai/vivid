"""Spec Engine v1: Rule-based node computation and spec generation."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from enum import Enum
import random


class NodeType(str, Enum):
    INPUT = "input"
    STYLE = "style"
    CUSTOMIZATION = "customization"
    PROCESSING = "processing"
    OUTPUT = "output"
    CAPSULE = "capsule"


# Default weights for spec components
DEFAULT_WEIGHTS = {
    "tension": 0.5,
    "pacing": "medium",
    "color_warmth": 0.5,
    "camera_dynamism": 0.5,
    "style_intensity": 0.6,
}


def compute_node(node: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a single node's output based on its type and inputs."""
    node_type = node.get("type", "customization")
    data = node.get("data", {})
    
    if node_type == NodeType.INPUT:
        # Input nodes pass through their data
        params = data.get("params", {}) if isinstance(data, dict) else {}
        return {
            "source_id": params.get("source_id") or params.get("sourceId") or data.get("source_id") or data.get("sourceId"),
            "character": params.get("character", data.get("character", "protagonist")),
            "emotion_curve": params.get("emotion_curve", data.get("emotion_curve", [0.3, 0.5, 0.7, 0.9, 0.6])),
            "scene_summary": params.get("scene_summary", data.get("scene_summary", "")),
            "duration_sec": params.get("duration_sec", data.get("duration_sec", 60)),
        }
    
    elif node_type == NodeType.CAPSULE:
        # Capsule nodes apply auteur-specific transformations
        params = data.get("params", {})
        pattern_version = (
            data.get("patternVersion") or data.get("pattern_version") or inputs.get("pattern_version")
        )
        style_intensity = params.get("style_intensity", 0.7)
        pacing = params.get("pacing", "medium")
        color_bias = params.get("color_bias", "neutral")
        camera_motion = params.get("camera_motion", "controlled")
        
        # Apply capsule transformations
        output = {
            **inputs,
            "pattern_version": pattern_version,
            "style_vector": _compute_style_vector(style_intensity, color_bias, camera_motion),
            "palette": _get_palette(color_bias),
            "composition_hints": _get_composition_hints(camera_motion),
            "pacing_hints": _get_pacing_hints(pacing),
        }
        for key in ("render_quality", "aspect_ratio", "lens", "film_stock", "time_of_day", "mood"):
            if key in params:
                output[key] = params[key]
        return output
    
    elif node_type == NodeType.STYLE:
        # Style nodes modify visual parameters
        params = data.get("params", {})
        style_intensity = params.get("style_intensity", inputs.get("style_intensity", DEFAULT_WEIGHTS["style_intensity"]))
        color_bias = params.get("color_bias", inputs.get("color_bias", "neutral"))
        composition = params.get("composition", inputs.get("composition", "rule_of_thirds"))
        pacing = params.get("pacing", inputs.get("pacing", DEFAULT_WEIGHTS["pacing"]))
        return {
            **inputs,
            "style_layer": params.get("style_layer", "base"),
            "style_intensity": style_intensity,
            "color_bias": color_bias,
            "composition": composition,
            "pacing": pacing,
        }
    
    elif node_type == NodeType.PROCESSING:
        # Processing nodes run optimization/generation
        params = data.get("params", {})
        seed = data.get("seed", {}) if isinstance(data, dict) else {}
        story_beats = seed.get("story_beats") or data.get("story_beats") or inputs.get("story_beats")
        storyboard_cards = (
            seed.get("storyboard_cards") or data.get("storyboard_cards") or inputs.get("storyboard_cards")
        )
        story_beats = story_beats if isinstance(story_beats, list) else []
        storyboard_cards = storyboard_cards if isinstance(storyboard_cards, list) else []
        mode = params.get("mode", "auto")
        return {
            **inputs,
            "processing_mode": mode,
            "target_profile": params.get("target_profile", "balanced"),
            "iterations": params.get("iterations", 10),
            "temperature": params.get("temperature", 0.7),
            "optimized": mode in ("ga", "rl"),
            "generation_ready": True,
            "story_beats": story_beats,
            "storyboard_cards": storyboard_cards,
        }

    elif node_type == NodeType.CUSTOMIZATION:
        # Customization nodes apply user preferences
        params = data.get("params", {})
        return {
            **inputs,
            "tone": params.get("tone", inputs.get("tone", "neutral")),
            "music_mood": params.get("music_mood", inputs.get("music_mood", "ambient")),
            "personal_theme": params.get("personal_theme", inputs.get("personal_theme", "")),
            "motif": params.get("motif", inputs.get("motif", "")),
        }
    
    elif node_type == NodeType.OUTPUT:
        # Output nodes finalize the spec
        beat_sheet = _generate_beat_sheet(inputs)
        storyboard = _generate_storyboard(inputs)
        shot_contracts = _generate_shot_contracts(inputs, storyboard)
        prompt_contracts = _generate_prompt_contracts(shot_contracts)
        render_quality = (
            inputs.get("render_quality")
            if isinstance(inputs.get("render_quality"), str)
            else data.get("quality", "preview")
        )
        return {
            **inputs,
            "final_spec": True,
            "render_quality": render_quality,
            "beat_sheet": beat_sheet,
            "storyboard": storyboard,
            "shot_contracts": shot_contracts,
            "prompt_contract_version": "v1",
            "prompt_contracts": prompt_contracts,
        }
    
    return inputs


def _compute_style_vector(intensity: float, color_bias: str, camera_motion: str) -> List[float]:
    """Generate a style embedding vector."""
    base = [intensity, intensity * 0.8, intensity * 0.9]
    
    # Color warmth
    if color_bias == "warm":
        base.extend([0.8, 0.4, 0.2])
    elif color_bias == "cool":
        base.extend([0.2, 0.4, 0.8])
    else:
        base.extend([0.5, 0.5, 0.5])
    
    # Camera dynamism
    if camera_motion == "dynamic":
        base.extend([0.9, 0.8])
    elif camera_motion == "static":
        base.extend([0.1, 0.2])
    else:
        base.extend([0.5, 0.5])
    
    return base


def _get_palette(color_bias: str) -> List[str]:
    """Get color palette based on bias."""
    palettes = {
        "warm": ["#FF6B35", "#F7931E", "#FFD23F", "#C44536", "#ED6A5A"],
        "cool": ["#2E4057", "#048A81", "#54C6EB", "#8EE3EF", "#7C8483"],
        "neutral": ["#2D3142", "#4F5D75", "#BFC0C0", "#FFFFFF", "#EF8354"],
    }
    return palettes.get(color_bias, palettes["neutral"])


def _get_composition_hints(camera_motion: str) -> List[str]:
    """Get composition hints based on camera motion."""
    hints = {
        "dynamic": ["dutch angle", "tracking shot", "handheld", "rack focus"],
        "controlled": ["symmetry", "rule of thirds", "leading lines", "dolly"],
        "static": ["centered", "wide shot", "fixed frame", "tableau"],
    }
    return hints.get(camera_motion, hints["controlled"])


def _get_pacing_hints(pacing: str) -> List[str]:
    """Get pacing hints."""
    hints = {
        "fast": ["quick cuts", "jump cuts", "<2s shots", "high tension"],
        "medium": ["balanced cuts", "3-5s shots", "varied rhythm"],
        "slow": ["long takes", ">5s shots", "lingering", "contemplative"],
    }
    return hints.get(pacing, hints["medium"])


def _generate_beat_sheet(inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a minimal beat sheet for MVP."""
    seeded = inputs.get("story_beats")
    if isinstance(seeded, list) and seeded:
        return seeded
    summary = inputs.get("scene_summary") or "Introduce the premise"
    tone = inputs.get("tone", "neutral")
    pacing = inputs.get("pacing", "medium")
    beats = [
        {"beat": "Setup", "note": summary},
        {"beat": "Inciting", "note": f"Shift the tone toward {tone}"},
        {"beat": "Turn", "note": f"Increase pace to {pacing}"},
        {"beat": "Climax", "note": "Deliver the core emotional payoff"},
        {"beat": "Resolution", "note": "Close with a clear visual motif"},
    ]
    return beats


def _generate_storyboard(inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a minimal storyboard preview for MVP."""
    seeded = inputs.get("storyboard_cards")
    if isinstance(seeded, list) and seeded:
        return seeded
    palette = inputs.get("palette", ["#333333", "#555555", "#777777"])
    compositions = inputs.get("composition_hints", ["wide shot", "close-up", "overhead"])
    pacing_hints = inputs.get("pacing_hints", ["balanced rhythm"])

    scenes = []
    for idx in range(3):
        scenes.append(
            {
                "shot": idx + 1,
                "composition": compositions[idx % len(compositions)],
                "dominant_color": palette[idx % len(palette)],
                "accent_color": palette[(idx + 1) % len(palette)],
                "pacing_note": pacing_hints[idx % len(pacing_hints)],
            }
        )
    return scenes


def _infer_shot_type(composition: str) -> str:
    if not isinstance(composition, str):
        return "medium"
    lowered = composition.lower()
    if "close" in lowered:
        return "close-up"
    if "wide" in lowered:
        return "wide"
    if "overhead" in lowered or "top" in lowered:
        return "overhead"
    if "medium" in lowered:
        return "medium"
    return "medium"


def _infer_duration(pacing: str) -> int:
    if pacing == "fast":
        return 2
    if pacing == "slow":
        return 5
    return 3


def _generate_shot_contracts(
    inputs: Dict[str, Any],
    storyboard: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not isinstance(storyboard, list):
        return []
    scene_id = str(inputs.get("scene_id") or inputs.get("sceneId") or "scene-01")
    sequence_id = str(inputs.get("sequence_id") or inputs.get("sequenceId") or "seq-01")
    work_id = inputs.get("work_id") or inputs.get("workId")
    character = str(inputs.get("character") or "PROTAGONIST")
    tone = str(inputs.get("tone") or "neutral")
    camera_motion = str(inputs.get("camera_motion") or "controlled")
    color_bias = str(inputs.get("color_bias") or "neutral")
    aspect_ratio = str(inputs.get("aspect_ratio") or "2.39:1")
    lens = str(inputs.get("lens") or "50mm anamorphic")
    film_stock = str(inputs.get("film_stock") or "Kodak Vision3 250D")
    lighting = str(inputs.get("lighting") or f"{color_bias} key light")
    time_of_day = str(inputs.get("time_of_day") or "day")
    palette = inputs.get("palette") if isinstance(inputs.get("palette"), list) else []
    pacing = str(inputs.get("pacing") or "medium")
    pose_motion = str(
        inputs.get("pose_motion")
        or ("moving through frame" if camera_motion == "dynamic" else "held stance")
    )
    dialogue = str(inputs.get("dialogue") or "")

    contracts: List[Dict[str, Any]] = []
    for idx, shot in enumerate(storyboard, start=1):
        if not isinstance(shot, dict):
            continue
        raw_shot = shot.get("shot_id") or shot.get("shot") or idx
        shot_id = (
            f"shot-{int(raw_shot):02d}"
            if isinstance(raw_shot, int)
            else str(raw_shot)
        )
        composition = str(shot.get("composition") or "framed composition")
        dominant = shot.get("dominant_color") or (palette[0] if palette else "#333333")
        accent = shot.get("accent_color") or (palette[1] if len(palette) > 1 else "#555555")
        shot_scene_id = str(shot.get("scene_id") or shot.get("sceneId") or scene_id)
        shot_sequence_id = str(shot.get("sequence_id") or shot.get("sequenceId") or sequence_id)
        shot_type = _infer_shot_type(composition)
        environment_layers = {
            "foreground": str(shot.get("foreground") or f"{composition} foreground detail"),
            "midground": str(shot.get("midground") or f"{character} framed in {composition}"),
            "background": str(shot.get("background") or "ambient environment"),
        }
        continuity_tags = [
            f"character:{character.lower()}",
            f"palette:{dominant}",
            f"camera:{camera_motion}",
        ]
        if isinstance(work_id, str) and work_id:
            continuity_tags.append(f"work:{work_id}")

        contracts.append(
            {
                "shot_id": shot_id,
                "sequence_id": shot_sequence_id,
                "scene_id": shot_scene_id,
                "shot_type": shot_type,
                "aspect_ratio": aspect_ratio,
                "lens": lens,
                "film_stock": film_stock,
                "lighting": lighting,
                "time_of_day": time_of_day,
                "mood": tone,
                "character": {
                    "name": character,
                    "age": inputs.get("character_age"),
                    "wardrobe": inputs.get("wardrobe"),
                    "notes": inputs.get("character_notes"),
                },
                "pose_motion": pose_motion,
                "dialogue": dialogue,
                "environment_layers": environment_layers,
                "continuity_tags": continuity_tags,
                "seed_image_ref": f"nb:storyboard:{shot_id}",
                "duration_sec": _infer_duration(pacing),
                "palette": {"primary": dominant, "accent": accent},
            }
        )
    return contracts


def _format_prompt_contract(shot: Dict[str, Any]) -> str:
    if not isinstance(shot, dict):
        return ""
    env = shot.get("environment_layers") if isinstance(shot.get("environment_layers"), dict) else {}
    character = shot.get("character") if isinstance(shot.get("character"), dict) else {}
    character_line = " ".join(
        [str(value) for value in [character.get("name"), character.get("wardrobe")] if value]
    ).strip()
    lines = [
        f"{shot.get('shot_type', 'medium')} shot, {shot.get('aspect_ratio', '2.39:1')}.",
        f"{shot.get('film_stock', 'cinematic')}, {shot.get('lighting', 'soft key light')}.",
        str(shot.get("lens", "50mm anamorphic")) + ".",
        character_line or "Protagonist in frame.",
        str(shot.get("pose_motion", "held stance")),
        f"Foreground: {env.get('foreground', '')}.",
        f"Midground: {env.get('midground', '')}.",
        f"Background: {env.get('background', '')}.",
        str(shot.get("mood", "")).strip(),
    ]
    dialogue = shot.get("dialogue")
    if isinstance(dialogue, str) and dialogue.strip():
        lines.append(f'Dialogue: "{dialogue.strip()}"')
    return " ".join([line for line in lines if line])


def _generate_prompt_contracts(shot_contracts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(shot_contracts, list):
        return []
    prompts: List[Dict[str, Any]] = []
    for shot in shot_contracts:
        if not isinstance(shot, dict):
            continue
        prompt = _format_prompt_contract(shot)
        prompts.append(
            {
                "shot_id": shot.get("shot_id"),
                "prompt": prompt,
            }
        )
    return prompts


def _merge_production_contract(
    spec: Dict[str, Any],
    graph_meta: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not isinstance(spec, dict) or not isinstance(graph_meta, dict):
        return spec
    production = graph_meta.get("production_contract")
    if not isinstance(production, dict):
        return spec
    merged = {**spec, "production_contract": production}
    shot_contracts = production.get("shot_contracts")
    if isinstance(shot_contracts, list) and shot_contracts:
        merged["shot_contracts"] = shot_contracts
    prompt_contracts = production.get("prompt_contracts")
    if isinstance(prompt_contracts, list) and prompt_contracts:
        merged["prompt_contracts"] = prompt_contracts
    prompt_version = production.get("prompt_contract_version")
    if isinstance(prompt_version, str) and prompt_version.strip():
        merged["prompt_contract_version"] = prompt_version.strip()
    return merged


def compute_graph(
    nodes: List[Dict],
    edges: List[Dict],
    graph_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute the entire graph and generate final spec."""
    # Build adjacency list
    adjacency: Dict[str, List[str]] = {}
    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        if src not in adjacency:
            adjacency[src] = []
        adjacency[src].append(tgt)
    
    # Build node map
    node_map = {node["id"]: node for node in nodes}
    
    # Find input nodes
    input_nodes = [n for n in nodes if n.get("type") == NodeType.INPUT]
    
    narrative_seeds: Dict[str, Any] = {}
    if isinstance(graph_meta, dict):
        meta_seeds = graph_meta.get("narrative_seeds")
        if isinstance(meta_seeds, dict):
            narrative_seeds = meta_seeds

    # Process in topological order (simplified BFS)
    outputs: Dict[str, Any] = {}
    queue = [n["id"] for n in input_nodes]
    visited = set()

    while queue:
        node_id = queue.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)
        
        node = node_map.get(node_id)
        if not node:
            continue
        
        # Collect inputs from predecessors
        inputs = {}
        for other_id, targets in adjacency.items():
            if node_id in targets and other_id in outputs:
                inputs.update(outputs[other_id])
        
        # Inject narrative seeds for output if missing upstream
        if node.get("type") == NodeType.OUTPUT and narrative_seeds:
            if "story_beats" not in inputs:
                seeded_beats = narrative_seeds.get("story_beats")
                if isinstance(seeded_beats, list) and seeded_beats:
                    inputs["story_beats"] = seeded_beats
            if "storyboard_cards" not in inputs:
                seeded_cards = narrative_seeds.get("storyboard_cards")
                if isinstance(seeded_cards, list) and seeded_cards:
                    inputs["storyboard_cards"] = seeded_cards

        # Compute this node
        outputs[node_id] = compute_node(node, inputs)
        
        # Add successors to queue
        for target_id in adjacency.get(node_id, []):
            queue.append(target_id)
    
    # Find output nodes and return their combined output
    output_nodes = [n for n in nodes if n.get("type") == NodeType.OUTPUT]
    if output_nodes:
        output_spec = outputs.get(output_nodes[0]["id"], {})
        return _merge_production_contract(output_spec, graph_meta)
    
    # If no output node, return last computed
    final_spec = outputs.get(list(outputs.keys())[-1], {}) if outputs else {}
    return _merge_production_contract(final_spec, graph_meta)


def generate_spec_from_canvas(canvas_data: Dict) -> Dict[str, Any]:
    """Generate a spec from canvas graph data."""
    nodes = canvas_data.get("nodes", [])
    edges = canvas_data.get("edges", [])
    meta = canvas_data.get("meta") if isinstance(canvas_data, dict) else None
    return compute_graph(nodes, edges, meta if isinstance(meta, dict) else None)
