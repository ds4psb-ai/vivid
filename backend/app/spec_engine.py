"""Spec Engine v1: Rule-based node computation and spec generation."""
from __future__ import annotations

from typing import Any, Dict, List
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
        return {
            "character": data.get("character", "protagonist"),
            "emotion_curve": data.get("emotion_curve", [0.3, 0.5, 0.7, 0.9, 0.6]),
            "scene_summary": data.get("scene_summary", ""),
            "duration_sec": data.get("duration_sec", 60),
        }
    
    elif node_type == NodeType.CAPSULE:
        # Capsule nodes apply auteur-specific transformations
        params = data.get("params", {})
        style_intensity = params.get("style_intensity", 0.7)
        pacing = params.get("pacing", "medium")
        color_bias = params.get("color_bias", "neutral")
        camera_motion = params.get("camera_motion", "controlled")
        
        # Apply capsule transformations
        return {
            **inputs,
            "style_vector": _compute_style_vector(style_intensity, color_bias, camera_motion),
            "palette": _get_palette(color_bias),
            "composition_hints": _get_composition_hints(camera_motion),
            "pacing_hints": _get_pacing_hints(pacing),
        }
    
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
        mode = params.get("mode", "auto")
        return {
            **inputs,
            "processing_mode": mode,
            "target_profile": params.get("target_profile", "balanced"),
            "iterations": params.get("iterations", 10),
            "temperature": params.get("temperature", 0.7),
            "optimized": mode in ("ga", "rl"),
            "generation_ready": True,
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
        return {
            **inputs,
            "final_spec": True,
            "render_quality": data.get("quality", "preview"),
            "beat_sheet": beat_sheet,
            "storyboard": storyboard,
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


def compute_graph(nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
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
        
        # Compute this node
        outputs[node_id] = compute_node(node, inputs)
        
        # Add successors to queue
        for target_id in adjacency.get(node_id, []):
            queue.append(target_id)
    
    # Find output nodes and return their combined output
    output_nodes = [n for n in nodes if n.get("type") == NodeType.OUTPUT]
    if output_nodes:
        return outputs.get(output_nodes[0]["id"], {})
    
    # If no output node, return last computed
    return outputs.get(list(outputs.keys())[-1], {}) if outputs else {}


def generate_spec_from_canvas(canvas_data: Dict) -> Dict[str, Any]:
    """Generate a spec from canvas graph data."""
    nodes = canvas_data.get("nodes", [])
    edges = canvas_data.get("edges", [])
    return compute_graph(nodes, edges)
