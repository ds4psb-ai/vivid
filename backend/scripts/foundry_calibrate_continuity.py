"""Grid search script for continuity score sub-weight calibration.

Evaluates different combinations of character, location, rhythm, and emotion
weights to find the best fit against the golden test set.
"""
from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BACKEND_DIR / "data" / "foundry" / "golden_continuity_test_set.json"


def calculate_continuity(
    *,
    context_characters: set[str],
    context_location: str,
    desired_rhythm: str,
    first_shot: dict,
    shots: list[dict],
    w_char: float,
    w_loc: float,
    w_rhythm: float,
    w_emotion: float,
) -> float:
    """Mirror of _calculate_continuity_score with configurable weights."""
    shot_characters = {str(c).lower() for c in (first_shot.get("characters") or [])}
    if context_characters and shot_characters:
        char_overlap = len(context_characters.intersection(shot_characters)) / max(
            len(context_characters.union(shot_characters)), 1
        )
    elif not context_characters:
        char_overlap = 1.0
    else:
        char_overlap = 0.0

    shot_location = str(first_shot.get("location") or "unknown").lower()
    if context_location == "unknown" or shot_location == "unknown":
        location_score = 0.7
    else:
        location_score = 1.0 if context_location == shot_location else 0.35

    movements = [str(s.get("camera_movement") or "static").lower() for s in shots]
    dynamic_count = sum(1 for m in movements if m in {"handheld", "tracking", "dolly", "whip_pan"})
    rhythm_ratio = dynamic_count / max(len(movements), 1)
    if desired_rhythm in {"dynamic", "aggressive"}:
        rhythm_score = rhythm_ratio
    elif desired_rhythm in {"steady", "calm"}:
        rhythm_score = 1.0 - rhythm_ratio
    else:
        rhythm_score = 1.0 - abs(rhythm_ratio - 0.5)

    emotion = str(first_shot.get("emotion_tone") or "neutral").lower()
    emotion_score = 1.0 if emotion in {"neutral", "balanced"} else 0.78
    if emotion in {"panic", "fear", "rage"} and desired_rhythm in {"steady", "calm"}:
        emotion_score = 0.4

    score = w_char * char_overlap + w_loc * location_score + w_rhythm * rhythm_score + w_emotion * emotion_score
    return max(0.0, min(round(score, 4), 1.0))


def main():
    if not DATA_PATH.exists():
        print(f"ERROR: Golden test set not found: {DATA_PATH}", flush=True)
        sys.exit(1)

    with open(DATA_PATH) as f:
        tests = json.load(f)

    print(f"Loaded {len(tests)} golden test cases", flush=True)

    # Grid search over weight combinations (must sum to 1.0)
    weight_options = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
    best_mae = float("inf")
    best_weights = None
    best_pass_rate = 0.0
    count = 0

    for w_char, w_loc, w_rhythm, w_emotion in product(weight_options, repeat=4):
        total = w_char + w_loc + w_rhythm + w_emotion
        if abs(total - 1.0) > 0.01:
            continue

        count += 1
        errors = []
        passes = 0
        for t in tests:
            ctx = t["scene_context"]
            first_shot = t["first_shot"]
            shots = t["candidate"].get("shots", [first_shot])

            actual = calculate_continuity(
                context_characters={str(c).lower() for c in (ctx.get("characters") or [])},
                context_location=str(ctx.get("location") or "unknown").lower(),
                desired_rhythm=str(ctx.get("desired_camera_rhythm") or "balanced").lower(),
                first_shot=first_shot,
                shots=shots,
                w_char=w_char,
                w_loc=w_loc,
                w_rhythm=w_rhythm,
                w_emotion=w_emotion,
            )
            diff = abs(actual - t["expected"])
            errors.append(diff)
            if diff <= t["tolerance"]:
                passes += 1

        mae = sum(errors) / len(errors)
        pass_rate = passes / len(tests)

        if pass_rate > best_pass_rate or (pass_rate == best_pass_rate and mae < best_mae):
            best_mae = mae
            best_weights = (w_char, w_loc, w_rhythm, w_emotion)
            best_pass_rate = pass_rate

    print(f"\nEvaluated {count} weight combinations", flush=True)
    print(f"\nBest weights:", flush=True)
    print(f"  char:    {best_weights[0]:.2f}", flush=True)
    print(f"  loc:     {best_weights[1]:.2f}", flush=True)
    print(f"  rhythm:  {best_weights[2]:.2f}", flush=True)
    print(f"  emotion: {best_weights[3]:.2f}", flush=True)
    print(f"  MAE:     {best_mae:.4f}", flush=True)
    print(f"  Pass:    {best_pass_rate*100:.1f}% ({int(best_pass_rate * len(tests))}/{len(tests)})", flush=True)

    # Show current production weights for comparison
    print(f"\nCurrent production weights: char=0.40, loc=0.25, rhythm=0.20, emotion=0.15", flush=True)


if __name__ == "__main__":
    main()
