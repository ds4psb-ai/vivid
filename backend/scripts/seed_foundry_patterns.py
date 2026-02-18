#!/usr/bin/env python3
"""Seed foundry_pattern_atoms with 2,000+ cinematic pattern atoms.

Usage:
    cd backend && python -m scripts.seed_foundry_patterns
    cd backend && python -m scripts.seed_foundry_patterns --count 2000 --batch 50
"""
from __future__ import annotations

import argparse
import asyncio
import random
import sys
import os
import uuid

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

random.seed(42)

# -- Template definitions ------------------------------------------------------

PATTERN_TYPES = ["composition", "camera_motion", "edit_rhythm", "emotion_arc", "dialogue_tension", "blocking"]

# Substitution pools
SUBJECTS = ["protagonist", "antagonist", "supporting character", "background figure", "key object", "silhouette"]
POSITIONS = ["left third", "right third", "upper-left", "lower-right", "center", "foreground", "background"]
ELEMENTS = ["leading line", "natural frame", "contrast edge", "light beam", "shadow", "arch", "doorway"]
FOCAL_POINTS = ["horizon", "subject's eyes", "key prop", "escape route", "threat source"]
CAMERA_MOVES = ["dolly in", "dolly out", "handheld push", "crane rise", "rack focus", "whip pan", "slow push"]
EMOTIONS = ["tension", "relief", "dread", "wonder", "melancholy", "euphoria", "isolation"]
CUT_LENGTHS = ["2 seconds", "4 seconds", "6 seconds", "8 seconds", "1 second", "3 seconds"]
SHOT_TYPES = ["close-up", "medium shot", "wide shot", "extreme close-up", "over-the-shoulder"]
LOCATIONS = ["doorway", "window", "staircase", "corridor", "open field", "confined space", "rooftop"]
ANTI_PATTERNS = [
    "overuse causes viewer fatigue",
    "avoid during calm expository scenes",
    "do not combine with fast editing",
    "loses impact when repeated consecutively",
    "breaks spatial continuity if overused",
    "creates tonal inconsistency in comedic scenes",
]
LICENSES = ["CC0", "CC_BY", "PUBLIC_DOMAIN", "EDUCATIONAL_USE", "RESEARCH_ONLY"]


TEMPLATES: dict[str, list[dict]] = {
    "composition": [
        {
            "tpl": "Rule of thirds: position {subject} at {position} intersection to create visual balance",
            "preconditions": ["single subject scene", "static or slow camera"],
            "effect": "visual harmony, natural eye movement along thirds grid",
        },
        {
            "tpl": "{element} guides viewer's eye toward {focal_point} using environmental geometry",
            "preconditions": ["architectural or natural environment", "clear foreground element"],
            "effect": "depth perception, directed attention toward focal subject",
        },
        {
            "tpl": "Frame {subject} within {location} to emphasize {emotion} through environmental context",
            "preconditions": ["meaningful location", "character-driven scene"],
            "effect": "thematic reinforcement, psychological depth",
        },
        {
            "tpl": "Silhouette {subject} against bright background at {position} for iconic visual impact",
            "preconditions": ["strong backlight source", "clear subject outline"],
            "effect": "mystery, power, iconic recognizability",
        },
        {
            "tpl": "Use {shot_type} with {subject} offset at {position} to suggest internal conflict",
            "preconditions": ["character introspective moment", "minimal camera movement"],
            "effect": "psychological tension, subtext visualization",
        },
        {
            "tpl": "Symmetrical composition centers {subject} in {location} to convey authority or vulnerability",
            "preconditions": ["symmetrical environment", "deliberate thematic intent"],
            "effect": "formal tension, power or isolation depending on context",
        },
        {
            "tpl": "Negative space on {position} side creates anticipation for {subject}'s movement",
            "preconditions": ["scene with implied movement", "directional staging"],
            "effect": "kinetic tension, visual breathing room",
        },
        {
            "tpl": "Dutch angle of 10-15 degrees with {subject} at {position} signals psychological instability",
            "preconditions": ["thriller or horror context", "character under threat"],
            "effect": "unease, disorientation, foreshadowing",
        },
    ],
    "camera_motion": [
        {
            "tpl": "{camera_move} toward {subject} during {emotion} peak to heighten intimacy",
            "preconditions": ["emotionally charged moment", "static subject"],
            "effect": "intensified emotional engagement, reduced physical distance",
        },
        {
            "tpl": "Hold static shot for {cut_length} before {camera_move} to build anticipation",
            "preconditions": ["moment of stillness before action", "deliberate pacing"],
            "effect": "tension buildup, payoff emphasis",
        },
        {
            "tpl": "Handheld shake during {subject} confrontation at {location} conveys instability",
            "preconditions": ["conflict scene", "naturalistic aesthetic"],
            "effect": "visceral realism, emotional rawness",
        },
        {
            "tpl": "Rack focus from {element} to {subject} reveals hidden information",
            "preconditions": ["layered foreground/background", "information reveal moment"],
            "effect": "narrative surprise, viewer reorientation",
        },
        {
            "tpl": "360-degree orbit around {subject} at {emotion} climax emphasizes isolation",
            "preconditions": ["open space staging", "emotional peak"],
            "effect": "environmental isolation, dramatic emphasis",
        },
        {
            "tpl": "Slow push into {shot_type} of {subject} during dialogue pause extracts subtext",
            "preconditions": ["dialogue scene", "character internal conflict"],
            "effect": "subtext surface, psychological depth",
        },
        {
            "tpl": "Match cut from {camera_move} to static wide reframes power dynamic",
            "preconditions": ["scene transition", "power shift narrative"],
            "effect": "visual contrast, tonal shift",
        },
        {
            "tpl": "Birds-eye descent to {shot_type} positions viewer as observer then participant",
            "preconditions": ["establishing scene", "God's eye to intimate shift"],
            "effect": "perspective transformation, empathy building",
        },
    ],
    "edit_rhythm": [
        {
            "tpl": "Cut every {cut_length} during {emotion} sequence to match physiological arousal",
            "preconditions": ["action or tension sequence", "clear emotional throughline"],
            "effect": "rhythmic alignment with viewer heartrate, immersion",
        },
        {
            "tpl": "J-cut: audio of next scene leads by {cut_length} before visual cut creates continuity",
            "preconditions": ["scene transition with audio bridge", "parallel narrative"],
            "effect": "seamless transition, audio-driven anticipation",
        },
        {
            "tpl": "L-cut: hold current visual {cut_length} after audio moves to next scene",
            "preconditions": ["dialogue scene exit", "contemplative moment"],
            "effect": "meditative transition, emotional residue",
        },
        {
            "tpl": "Jump cut series of {cut_length} intervals shows time compression during {emotion}",
            "preconditions": ["time-lapse narrative", "French New Wave aesthetic context"],
            "effect": "temporal disorientation, energy injection",
        },
        {
            "tpl": "Long take of {cut_length} without cut builds credibility and {emotion}",
            "preconditions": ["performance-driven scene", "Steadicam or locked-off"],
            "effect": "authenticity, unbroken tension",
        },
        {
            "tpl": "Cross-cut between {subject} and {focal_point} every {cut_length} escalates parallel action",
            "preconditions": ["parallel narrative", "converging storylines"],
            "effect": "suspense escalation, temporal compression",
        },
    ],
    "emotion_arc": [
        {
            "tpl": "Escalate from {shot_type} to extreme close-up across three beats to amplify {emotion}",
            "preconditions": ["three-beat scene structure", "single character focus"],
            "effect": "graduated intimacy, emotional crescendo",
        },
        {
            "tpl": "Reverse arc from close-up to wide shot after {emotion} peak signals emotional release",
            "preconditions": ["post-climax scene", "space available for revelation"],
            "effect": "catharsis, environmental contextualization",
        },
        {
            "tpl": "Maintain {shot_type} during {emotion} transition to let performance carry the shift",
            "preconditions": ["actor-driven moment", "minimal intervention aesthetic"],
            "effect": "performance centrality, naturalistic emotion",
        },
        {
            "tpl": "Cut to {subject} reaction {cut_length} after trigger event to delay {emotion} payoff",
            "preconditions": ["reaction shot opportunity", "delayed reveal strategy"],
            "effect": "suspense extension, emotional investment",
        },
        {
            "tpl": "Hold on {subject} face for {cut_length} as {emotion} registers without dialogue",
            "preconditions": ["wordless moment", "strong performer"],
            "effect": "pure visual storytelling, viewer projection",
        },
    ],
    "dialogue_tension": [
        {
            "tpl": "Shoot {subject} with {shot_type} during power dialogue, {focal_point} in soft background",
            "preconditions": ["two-person dialogue", "power imbalance scene"],
            "effect": "dominance visualization, environmental subordination",
        },
        {
            "tpl": "Cut to {subject}'s hands or {element} during key dialogue line to suggest subtext",
            "preconditions": ["layered dialogue scene", "character concealing information"],
            "effect": "subtext externalization, viewer curiosity",
        },
        {
            "tpl": "Over-the-shoulder {shot_type} holds {cut_length} longer than expected before reverse",
            "preconditions": ["confrontational dialogue", "dominant/submissive dynamic"],
            "effect": "power asymmetry, discomfort amplification",
        },
        {
            "tpl": "Single shot two-person dialogue without cuts for {cut_length} creates theatrical tension",
            "preconditions": ["stage-like staging", "strong performances"],
            "effect": "theatrical authenticity, unbroken performance",
        },
        {
            "tpl": "Insert {shot_type} of {element} between dialogue lines reveals what speaker conceals",
            "preconditions": ["information asymmetry scene", "character deception"],
            "effect": "dramatic irony, viewer omniscience",
        },
    ],
    "blocking": [
        {
            "tpl": "{subject} crosses to {position} as power dynamic shifts, changing spatial dominance",
            "preconditions": ["power shift scene", "open staging area"],
            "effect": "physical power visualization, spatial storytelling",
        },
        {
            "tpl": "Place {subject} at {location} with {element} as physical barrier to show separation",
            "preconditions": ["emotional distance scene", "meaningful props available"],
            "effect": "physical metaphor for emotional state, visual subtext",
        },
        {
            "tpl": "{subject} and {focal_point} mirror body language at {location} showing alignment",
            "preconditions": ["alliance or empathy scene", "rehearsed choreography"],
            "effect": "visual harmony, relationship shorthand",
        },
        {
            "tpl": "Stage {subject} with back to camera at {position} during moment of vulnerability",
            "preconditions": ["vulnerability reveal scene", "character at breaking point"],
            "effect": "viewer identification, body language intimacy",
        },
        {
            "tpl": "Dynamic blocking: {subject} moves from {position} to {location} while delivering key line",
            "preconditions": ["kinetic performance style", "motivated movement"],
            "effect": "energy injection, action-word synchrony",
        },
    ],
}


def _fill_template(template_data: dict, pattern_type: str) -> dict:
    tpl = template_data["tpl"]

    substitutions = {
        "subject": random.choice(SUBJECTS),
        "position": random.choice(POSITIONS),
        "element": random.choice(ELEMENTS),
        "focal_point": random.choice(FOCAL_POINTS),
        "camera_move": random.choice(CAMERA_MOVES),
        "emotion": random.choice(EMOTIONS),
        "cut_length": random.choice(CUT_LENGTHS),
        "shot_type": random.choice(SHOT_TYPES),
        "location": random.choice(LOCATIONS),
    }

    try:
        execution_template = tpl.format(**substitutions)
    except KeyError:
        execution_template = tpl  # fallback

    preconditions = template_data.get("preconditions", [])
    expected_effect = template_data.get("effect", "visual impact")
    anti_pattern = random.choice(ANTI_PATTERNS)
    source_license = random.choice(LICENSES)

    return {
        "pattern_type": pattern_type,
        "preconditions": preconditions,
        "execution_template": execution_template,
        "expected_effect": expected_effect,
        "anti_pattern": anti_pattern,
        "source_license": source_license,
    }


def generate_atoms(count: int) -> list[dict]:
    atoms = []
    per_type = count // len(PATTERN_TYPES)
    remainder = count - per_type * len(PATTERN_TYPES)

    for i, pattern_type in enumerate(PATTERN_TYPES):
        type_count = per_type + (1 if i < remainder else 0)
        templates = TEMPLATES[pattern_type]
        for j in range(type_count):
            tpl_data = templates[j % len(templates)]
            atoms.append(_fill_template(tpl_data, pattern_type))

    return atoms


TRANSITION_TEMPLATES = [
    "Cut from {shot_type_a} to {shot_type_b} on motion match for seamless continuity",
    "Smash cut from quiet {shot_type_a} to loud {shot_type_b} for shock effect",
    "Dissolve over {duration} seconds from {shot_type_a} to {shot_type_b} signals time passage",
    "Wipe from {shot_type_a} reveals {shot_type_b} for genre-appropriate transition",
    "Match dissolve: {element_a} morphs to {element_b} across scene boundary",
]

SHOT_TYPE_A = ["extreme wide", "medium", "close-up", "POV", "overhead"]
SHOT_TYPE_B = ["close-up", "wide", "medium", "reaction", "insert"]
DURATIONS = ["0.5", "1", "2", "3"]
ELEMENTS_A = ["circular object", "door", "clock", "face", "window"]
ELEMENTS_B = ["sun", "portal", "timepiece", "landscape", "frame"]


def generate_transition_rules(count: int = 500) -> list[dict]:
    rules = []
    for i in range(count):
        tpl = TRANSITION_TEMPLATES[i % len(TRANSITION_TEMPLATES)]
        text = tpl.format(
            shot_type_a=random.choice(SHOT_TYPE_A),
            shot_type_b=random.choice(SHOT_TYPE_B),
            duration=random.choice(DURATIONS),
            element_a=random.choice(ELEMENTS_A),
            element_b=random.choice(ELEMENTS_B),
        )
        rules.append({
            "rule_type": "transition",
            "execution_template": text,
            "compatible_from": random.choice(SHOT_TYPE_A),
            "compatible_to": random.choice(SHOT_TYPE_B),
            "source_license": random.choice(LICENSES),
            "tenant_id": "system",
            "project_id": "foundry_seed",
        })
    return rules


async def seed_patterns(count: int = 2000, batch_size: int = 50):
    from app.services.embedder import get_embedder
    from app.config import settings
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models

    embedder = get_embedder()
    qdrant_api_key = settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None
    client = QdrantClient(url=settings.QDRANT_URL, api_key=qdrant_api_key, timeout=60)

    # Generate atoms
    atoms = generate_atoms(count)
    print(f"Generated {len(atoms)} pattern atoms", flush=True)

    # Batch upsert to foundry_pattern_atoms
    total = 0
    for i in range(0, len(atoms), batch_size):
        batch = atoms[i:i + batch_size]
        texts = [
            f"{a['pattern_type']}: {a['execution_template']} -> {a['expected_effect']}"
            for a in batch
        ]
        vectors = embedder.embed_batch(texts)

        points = [
            qdrant_models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={**atom, "tenant_id": "system", "project_id": "foundry_seed"},
            )
            for atom, vec in zip(batch, vectors)
        ]

        client.upsert(collection_name="foundry_pattern_atoms", points=points, wait=True)
        total += len(batch)
        if total % 200 == 0 or total == len(atoms):
            print(f"Pattern atoms: {total}/{len(atoms)}", flush=True)

    # Seed transition rules
    print("Seeding transition rules...", flush=True)
    rules = generate_transition_rules(500)
    rule_total = 0
    for i in range(0, len(rules), batch_size):
        batch = rules[i:i + batch_size]
        texts = [r["execution_template"] for r in batch]
        vectors = embedder.embed_batch(texts)
        points = [
            qdrant_models.PointStruct(id=str(uuid.uuid4()), vector=vec, payload=rule)
            for rule, vec in zip(batch, vectors)
        ]
        client.upsert(collection_name="foundry_transition_rules", points=points, wait=True)
        rule_total += len(batch)

    print(f"Transition rules: {rule_total}", flush=True)
    print(f"Seeding complete: {total} pattern atoms + {rule_total} transition rules", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed foundry pattern atoms")
    parser.add_argument("--count", type=int, default=2000, help="Number of pattern atoms")
    parser.add_argument("--batch", type=int, default=50, help="Batch size")
    args = parser.parse_args()
    asyncio.run(seed_patterns(args.count, args.batch))
