"""GA Prototype: Genetic Algorithm for spec optimization."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple
from copy import deepcopy


# Mutation ranges for parameters
PARAM_RANGES = {
    "style_intensity": (0.4, 1.0),
    "tension_bias": (0.0, 1.0),
    "symmetry_bias": (0.0, 1.0),
    "light_diffusion": (0.0, 1.0),
    "music_sync": (0.0, 1.0),
    "chaos_bias": (0.0, 1.0),
    "stillness": (0.0, 1.0),
}

PACING_OPTIONS = ["slow", "medium", "fast"]
COLOR_BIAS_OPTIONS = ["cool", "neutral", "warm"]
CAMERA_MOTION_OPTIONS = ["static", "controlled", "dynamic"]


def mutate_params(params: Dict[str, Any], mutation_rate: float = 0.3) -> Dict[str, Any]:
    """Apply random mutations to parameters."""
    mutated = deepcopy(params)
    
    for key, value in mutated.items():
        if random.random() > mutation_rate:
            continue
            
        if key in PARAM_RANGES:
            # Numeric mutation with gaussian noise
            min_val, max_val = PARAM_RANGES[key]
            noise = random.gauss(0, 0.1)
            new_val = max(min_val, min(max_val, value + noise))
            mutated[key] = round(new_val, 2)
        elif key == "pacing":
            mutated[key] = random.choice(PACING_OPTIONS)
        elif key == "color_bias":
            mutated[key] = random.choice(COLOR_BIAS_OPTIONS)
        elif key == "camera_motion":
            mutated[key] = random.choice(CAMERA_MOTION_OPTIONS)
    
    return mutated


def crossover(parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
    """Combine two parent parameter sets."""
    child = {}
    all_keys = set(parent1.keys()) | set(parent2.keys())
    
    for key in all_keys:
        if key in parent1 and key in parent2:
            # Random selection
            child[key] = random.choice([parent1[key], parent2[key]])
        elif key in parent1:
            child[key] = parent1[key]
        else:
            child[key] = parent2[key]
    
    return child


def _estimate_complexity_proxy(params: Dict[str, Any]) -> float:
    """Estimate relative cost/latency proxy from params (0~1)."""
    score = 0.0
    style_intensity = params.get("style_intensity")
    if isinstance(style_intensity, (int, float)):
        score += max(0.0, min(float(style_intensity), 1.0))

    pacing = params.get("pacing")
    if pacing == "fast":
        score += 0.2
    elif pacing == "slow":
        score -= 0.1

    camera = params.get("camera_motion")
    if camera == "dynamic":
        score += 0.2
    elif camera == "static":
        score -= 0.1

    chaos_bias = params.get("chaos_bias")
    if isinstance(chaos_bias, (int, float)):
        score += max(0.0, min(float(chaos_bias), 1.0)) * 0.1

    return max(0.0, min(score, 1.0))


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, float(v)) for v in weights.values())
    if total <= 0:
        return weights
    return {k: max(0.0, float(v)) / total for k, v in weights.items()}


def _resolve_objective_weights(objective: Optional[str], weights: Optional[Dict[str, float]]) -> Dict[str, float]:
    if weights:
        return _normalize_weights(weights)
    objective = (objective or "balanced").strip().lower()
    presets = {
        "balanced": {"quality": 0.6, "cost": 0.2, "latency": 0.2},
        "quality": {"quality": 0.8, "cost": 0.1, "latency": 0.1},
        "efficient": {"quality": 0.4, "cost": 0.3, "latency": 0.3},
        "cost": {"quality": 0.3, "cost": 0.5, "latency": 0.2},
        "latency": {"quality": 0.3, "cost": 0.2, "latency": 0.5},
    }
    return presets.get(objective, presets["balanced"])


def fitness_function(
    params: Dict[str, Any],
    target_profile: str = "balanced",
    objective: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Calculate fitness score for a parameter set."""
    score = 0.0
    
    # Base score from style intensity
    style_intensity = params.get("style_intensity", 0.5)
    score += style_intensity * 20
    
    # Profile-specific scoring
    if target_profile == "dramatic":
        score += params.get("tension_bias", 0) * 15
        score += params.get("chaos_bias", 0) * 10
        if params.get("pacing") == "fast":
            score += 10
        if params.get("camera_motion") == "dynamic":
            score += 8
    
    elif target_profile == "lyrical":
        score += params.get("light_diffusion", 0) * 15
        score += params.get("stillness", 0) * 10
        if params.get("pacing") == "slow":
            score += 10
        if params.get("color_bias") == "warm":
            score += 8
    
    elif target_profile == "rhythmic":
        score += params.get("music_sync", 0) * 20
        if params.get("pacing") == "medium":
            score += 10
        if params.get("camera_motion") == "dynamic":
            score += 10
    
    else:  # balanced
        # Reward moderate values
        for key, value in params.items():
            if isinstance(value, (int, float)):
                # Penalize extremes
                distance_from_center = abs(value - 0.5)
                score += (1 - distance_from_center) * 5
    
    # Add some randomness to avoid local optima
    score += random.gauss(0, 2)
    
    quality_score = max(0.0, score)
    proxy = _estimate_complexity_proxy(params)
    weight_map = _resolve_objective_weights(objective, weights)
    quality_norm = min(quality_score / 100.0, 1.0)
    cost_score = 1.0 - proxy
    latency_score = 1.0 - proxy

    combined = (
        quality_norm * weight_map.get("quality", 0.0)
        + cost_score * weight_map.get("cost", 0.0)
        + latency_score * weight_map.get("latency", 0.0)
    )
    return max(0.0, combined * 100.0)


def evidence_based_fitness(
    params: Dict[str, Any],
    run_metrics: Dict[str, Any],
    pattern_lifts: Optional[Dict[str, float]] = None,
) -> float:
    """Calculate fitness score from actual evidence/run metrics.
    
    Args:
        params: The parameter set used for the capsule run.
        run_metrics: Metrics from actual execution including:
            - evidence_count: Number of evidence refs in output
            - token_usage: Total tokens consumed
            - latency_ms: Execution time in milliseconds
            - user_feedback: Optional user rating (1-5)
            - completion_rate: Optional (0.0-1.0)
            - pattern_names: Optional list of pattern names used
        pattern_lifts: Optional dict mapping pattern_name -> lift value.
            If provided, patterns with positive lift get bonus points.
    
    Returns:
        Evidence-based fitness score.
    
    Reference:
        07_EXECUTION_PLAN_2025-12.md Phase 2.2
    """
    score = 0.0
    
    # Evidence quality (most important)
    evidence_count = run_metrics.get("evidence_count", 0)
    if evidence_count > 0:
        score += min(evidence_count * 5, 25)  # Cap at 25 points
    
    # Efficiency (lower tokens = better)
    token_usage = run_metrics.get("token_usage", 0)
    if token_usage > 0:
        # Reward efficient token usage (baseline: 1000 tokens)
        efficiency_ratio = min(1000 / token_usage, 1.5)
        score += efficiency_ratio * 10
    
    # Latency (lower = better)
    latency_ms = run_metrics.get("latency_ms", 0)
    if latency_ms > 0:
        # Reward fast execution (baseline: 5000ms)
        speed_ratio = min(5000 / latency_ms, 2.0)
        score += speed_ratio * 10
    
    # User feedback (if available)
    user_feedback = run_metrics.get("user_feedback")
    if user_feedback is not None:
        # Scale 1-5 to 0-25 points
        score += (user_feedback - 1) * 6.25
    
    # Completion rate
    completion_rate = run_metrics.get("completion_rate", 1.0)
    score += completion_rate * 10
    
    # Pattern version bonus (runs with newer patterns get slight bonus)
    pattern_version = run_metrics.get("pattern_version", "v0")
    version_num = int(pattern_version.replace("v", "")) if pattern_version.startswith("v") else 0
    score += min(version_num, 5)  # Cap bonus at 5 points
    
    # === NEW: Pattern Lift Bonus (Phase 2.2) ===
    # Patterns with positive lift values get bonus fitness points
    # This encourages the GA to favor parameter sets associated with high-lift patterns
    if pattern_lifts:
        pattern_names = run_metrics.get("pattern_names", [])
        if isinstance(pattern_names, list):
            lift_bonus = 0.0
            for pattern_name in pattern_names:
                if pattern_name in pattern_lifts:
                    lift_value = pattern_lifts[pattern_name]
                    # Scale lift to bonus: +10% lift = +2 points, max +10 points per pattern
                    if lift_value > 0:
                        lift_bonus += min(lift_value * 20, 10)
            # Cap total lift bonus at 20 points
            score += min(lift_bonus, 20)
    
    return max(0, score)


def run_ga(
    initial_params: Dict[str, Any],
    target_profile: str = "balanced",
    population_size: int = 20,
    generations: int = 10,
    top_k: int = 3,
    mutation_rate: float = 0.5,
    early_stop_patience: int = 3,
    min_improvement: float = 0.5,
    objective: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Run genetic algorithm optimization with adaptive mutation and early stopping.
    
    Returns top_k parameter sets with their fitness scores.
    """
    # Initialize population with mutations of initial params
    population = [initial_params]
    for _ in range(population_size - 1):
        population.append(mutate_params(initial_params, mutation_rate=mutation_rate))

    best_score = float("-inf")
    stalled = 0

    for gen in range(generations):
        # Adaptive mutation: cool down over time
        if generations > 1:
            progress = gen / (generations - 1)
        else:
            progress = 1.0
        adaptive_rate = max(0.1, mutation_rate * (1.0 - progress))

        # Calculate fitness for all individuals
        scored = [
            (ind, fitness_function(ind, target_profile, objective, weights))
            for ind in population
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        current_best = scored[0][1] if scored else float("-inf")
        if current_best - best_score >= min_improvement:
            best_score = current_best
            stalled = 0
        else:
            stalled += 1
        if early_stop_patience > 0 and stalled >= early_stop_patience:
            break
        
        # Selection: keep top 50%
        survivors = [ind for ind, _ in scored[: max(2, population_size // 2)]]
        
        # Reproduction
        new_population = list(survivors)
        
        while len(new_population) < population_size:
            parent1, parent2 = random.sample(survivors, 2)
            child = crossover(parent1, parent2)
            child = mutate_params(child, mutation_rate=adaptive_rate)
            new_population.append(child)
        
        population = new_population
    
    # Final scoring and selection
    scored = [
        (ind, fitness_function(ind, target_profile, objective, weights))
        for ind in population
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[:top_k]


def optimize_canvas_params(
    canvas_data: Dict[str, Any],
    target_profile: str = "balanced",
    objective: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Optimize parameters for a canvas using GA.
    
    Returns top 3 recommended parameter variations.
    """
    nodes = canvas_data.get("nodes", [])
    
    # Find capsule nodes
    capsule_nodes = [n for n in nodes if n.get("type") == "capsule"]
    
    if not capsule_nodes:
        return []
    
    # Get current params from first capsule
    current_params = capsule_nodes[0].get("data", {}).get("params", {})
    
    if not current_params:
        current_params = {
            "style_intensity": 0.7,
            "pacing": "medium",
            "color_bias": "neutral",
            "camera_motion": "controlled",
        }
    
    # Run GA
    results = run_ga(
        current_params,
        target_profile,
        top_k=3,
        objective=objective,
        weights=weights,
    )
    
    # Format recommendations
    recommendations = []
    for params, score in results:
        recommendations.append({
            "params": params,
            "fitness_score": round(score, 2),
            "profile": target_profile,
        })
    
    return recommendations
