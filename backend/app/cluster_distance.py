"""Cluster distance calculation for pattern grouping.

Implements D = 0.55*DL + 0.35*DP + 0.10*DC formula from the architecture docs.

DL: Logic vector cosine distance
DP: Persona vector cosine distance  
DC: Context similarity (temporal_phase, motif overlap)
"""
import math
from typing import Optional


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))
    
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    
    return dot_product / (magnitude_a * magnitude_b)


def cosine_distance(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculate cosine distance (1 - similarity) between two vectors."""
    return 1.0 - cosine_similarity(vec_a, vec_b)


def context_distance(context_a: dict, context_b: dict) -> float:
    """
    Calculate context distance based on temporal_phase and motif overlap.
    
    Returns 0.0 (identical) to 1.0 (completely different)
    """
    score = 0.0
    
    # Temporal phase match (50% of context score)
    phase_a = context_a.get("temporal_phase", "")
    phase_b = context_b.get("temporal_phase", "")
    if phase_a != phase_b:
        score += 0.5
    
    # Motif overlap (50% of context score)
    motifs_a = set(context_a.get("motifs", []))
    motifs_b = set(context_b.get("motifs", []))
    
    if motifs_a or motifs_b:
        intersection = len(motifs_a & motifs_b)
        union = len(motifs_a | motifs_b)
        motif_similarity = intersection / union if union > 0 else 0.0
        score += 0.5 * (1.0 - motif_similarity)
    
    return score


def calculate_cluster_distance(
    logic_vector_a: list[float],
    logic_vector_b: list[float],
    persona_vector_a: list[float],
    persona_vector_b: list[float],
    context_a: dict,
    context_b: dict,
) -> float:
    """
    Calculate composite cluster distance using weighted formula.
    
    D = 0.55*DL + 0.35*DP + 0.10*DC
    
    Args:
        logic_vector_a: Logic vector for item A
        logic_vector_b: Logic vector for item B
        persona_vector_a: Persona vector for item A
        persona_vector_b: Persona vector for item B
        context_a: Context dict with temporal_phase, motifs for item A
        context_b: Context dict with temporal_phase, motifs for item B
        
    Returns:
        Distance score from 0.0 (identical) to 1.0 (completely different)
    """
    DL = cosine_distance(logic_vector_a, logic_vector_b)
    DP = cosine_distance(persona_vector_a, persona_vector_b)
    DC = context_distance(context_a, context_b)
    
    return 0.55 * DL + 0.35 * DP + 0.10 * DC


def should_same_cluster(
    distance: float,
    threshold: float = 0.35,
) -> bool:
    """
    Determine if two items should be in the same cluster.
    
    Args:
        distance: Calculated cluster distance
        threshold: Maximum distance for same cluster (default 0.35, tunable 0.30-0.40)
        
    Returns:
        True if items should be in the same cluster
    """
    return distance <= threshold


def validate_cluster_assignment(
    item: dict,
    cluster_items: list[dict],
    threshold: float = 0.35,
) -> dict:
    """
    Validate if an item should be assigned to an existing cluster.
    
    Args:
        item: Item to validate with logic_vector, persona_vector, context
        cluster_items: Existing items in the cluster
        threshold: Distance threshold for cluster membership
        
    Returns:
        {
            "should_join": bool,
            "avg_distance": float,
            "min_distance": float,
            "max_distance": float,
            "distances": list[float]
        }
    """
    if not cluster_items:
        return {
            "should_join": True,
            "avg_distance": 0.0,
            "min_distance": 0.0,
            "max_distance": 0.0,
            "distances": [],
        }
    
    distances = []
    for cluster_item in cluster_items:
        dist = calculate_cluster_distance(
            logic_vector_a=item.get("logic_vector", []),
            logic_vector_b=cluster_item.get("logic_vector", []),
            persona_vector_a=item.get("persona_vector", []),
            persona_vector_b=cluster_item.get("persona_vector", []),
            context_a=item.get("context", {}),
            context_b=cluster_item.get("context", {}),
        )
        distances.append(dist)
    
    avg_distance = sum(distances) / len(distances)
    
    return {
        "should_join": avg_distance <= threshold,
        "avg_distance": avg_distance,
        "min_distance": min(distances),
        "max_distance": max(distances),
        "distances": distances,
    }


# Hard gates from architecture docs
def check_hard_gates(
    item_a: dict,
    item_b: dict,
) -> dict:
    """
    Check hard gates that block same-cluster assignment regardless of distance.
    
    Hard Gate 1: Different temporal_phase = cannot be same cluster
    Hard Gate 2: Core motifs/rules differ by 2+ = new cluster
    
    Returns:
        {
            "pass": bool,
            "reason": Optional[str]
        }
    """
    # Hard Gate 1: Temporal phase must match
    phase_a = item_a.get("context", {}).get("temporal_phase", "")
    phase_b = item_b.get("context", {}).get("temporal_phase", "")
    
    if phase_a and phase_b and phase_a != phase_b:
        return {
            "pass": False,
            "reason": f"temporal_phase mismatch: {phase_a} vs {phase_b}"
        }
    
    # Hard Gate 2: Core motifs must have at least 2 in common
    core_motifs_a = set(item_a.get("context", {}).get("core_motifs", []))
    core_motifs_b = set(item_b.get("context", {}).get("core_motifs", []))
    
    if core_motifs_a and core_motifs_b:
        common = len(core_motifs_a & core_motifs_b)
        if common < 2:
            return {
                "pass": False,
                "reason": f"core_motifs overlap < 2: {common} common motifs"
            }
    
    return {"pass": True, "reason": None}
