"""Cinematic Technique RAG Layer.

AD Studio용 영화 기법 코퍼스 쿼리 레이어.
JSON 코퍼스를 로드하여 무드 기반 기법 추천, 전환 제안 등 제공.

Usage:
    from app.rag.cinematic_techniques import (
        query_techniques,
        get_technique_by_id,
        get_all_techniques,
        suggest_transitions,
    )

    # 무드 기반 기법 추천
    matches = query_techniques("tension")

    # ID로 기법 조회
    technique = get_technique_by_id("chiaroscuro")

    # 씬 간 전환 제안
    transitions = suggest_transitions("tension", "serenity")
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class Technique:
    """Single cinematic technique entry."""

    technique_id: str
    category: str
    name_ko: str
    name_en: str
    description_ko: str
    visual_effect_ko: str
    best_for: List[str]
    prompt_keywords: Dict[str, str]
    combinable_with: List[str]
    source_refs: List[str]

    def to_dict(self) -> Dict:
        return {
            "technique_id": self.technique_id,
            "category": self.category,
            "name_ko": self.name_ko,
            "name_en": self.name_en,
            "description_ko": self.description_ko,
            "visual_effect_ko": self.visual_effect_ko,
            "best_for": self.best_for,
            "prompt_keywords": self.prompt_keywords,
            "combinable_with": self.combinable_with,
            "source_refs": self.source_refs,
        }


@dataclass
class TechniqueMatch:
    """Technique match result with relevance score."""

    technique: Technique
    score: float
    match_reason: str

    def to_dict(self) -> Dict:
        return {
            **self.technique.to_dict(),
            "score": self.score,
            "match_reason": self.match_reason,
        }


@dataclass
class TransitionSuggestion:
    """Transition suggestion between two scenes."""

    technique: Technique
    score: float
    reasoning_ko: str

    def to_dict(self) -> Dict:
        return {
            **self.technique.to_dict(),
            "score": self.score,
            "reasoning_ko": self.reasoning_ko,
        }


# =============================================================================
# Corpus Loading (module-level singleton)
# =============================================================================

_corpus_data: Optional[Dict] = None
_techniques: Dict[str, Technique] = {}
_mood_map: Dict[str, List[str]] = {}
_transition_mood_map: Dict[str, List[str]] = {}

CORPUS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rag_docs" / "cinematic" / "techniques_corpus.json"


def _load_corpus() -> None:
    """Load technique corpus from JSON file."""
    global _corpus_data, _techniques, _mood_map, _transition_mood_map

    if _corpus_data is not None:
        return

    if not CORPUS_PATH.exists():
        logger.warning(f"Cinematic techniques corpus not found: {CORPUS_PATH}")
        _corpus_data = {}
        return

    try:
        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            _corpus_data = json.load(f)

        for entry in _corpus_data.get("techniques", []):
            technique = Technique(
                technique_id=entry["technique_id"],
                category=entry["category"],
                name_ko=entry["name_ko"],
                name_en=entry["name_en"],
                description_ko=entry["description_ko"],
                visual_effect_ko=entry["visual_effect_ko"],
                best_for=entry.get("best_for", []),
                prompt_keywords=entry.get("prompt_keywords", {}),
                combinable_with=entry.get("combinable_with", []),
                source_refs=entry.get("source_refs", ["internal"]),
            )
            _techniques[technique.technique_id] = technique

        _mood_map = _corpus_data.get("mood_technique_map", {})
        _transition_mood_map = _corpus_data.get("transition_mood_map", {})

        logger.info(
            f"Loaded {len(_techniques)} cinematic techniques, "
            f"{len(_mood_map)} mood mappings"
        )
    except Exception as e:
        logger.error(f"Failed to load cinematic techniques corpus: {e}")
        _corpus_data = {}


# Eagerly load on import
_load_corpus()


# =============================================================================
# Query Functions
# =============================================================================

def query_techniques(
    mood: str,
    category: Optional[str] = None,
    top_k: int = 10,
) -> List[TechniqueMatch]:
    """Query techniques by mood keyword with optional category filter.

    Uses the mood_technique_map for direct matches, then falls back
    to keyword matching against descriptions and best_for fields.

    Args:
        mood: Mood keyword (e.g. "tension", "serenity", "power").
        category: Optional category filter (e.g. "composition", "lighting").
        top_k: Maximum results to return.

    Returns:
        Ranked list of TechniqueMatch.
    """
    _load_corpus()
    results: List[TechniqueMatch] = []
    mood_lower = mood.lower().strip()

    # 1) Direct mood map lookup
    mapped_ids = _mood_map.get(mood_lower, [])
    for idx, tid in enumerate(mapped_ids):
        technique = _techniques.get(tid)
        if technique is None:
            continue
        if category and technique.category != category:
            continue
        results.append(TechniqueMatch(
            technique=technique,
            score=1.0 - (idx * 0.05),  # ordered by relevance in map
            match_reason=f"mood_map:{mood_lower}",
        ))

    seen_ids = {m.technique.technique_id for m in results}

    # 2) Keyword fallback: match against best_for, description, visual_effect
    for technique in _techniques.values():
        if technique.technique_id in seen_ids:
            continue
        if category and technique.category != category:
            continue

        score = _keyword_score(mood_lower, technique)
        if score > 0:
            results.append(TechniqueMatch(
                technique=technique,
                score=score,
                match_reason="keyword_match",
            ))

    results.sort(key=lambda m: m.score, reverse=True)
    return results[:top_k]


def get_technique_by_id(technique_id: str) -> Optional[Technique]:
    """Get a single technique by its ID.

    Args:
        technique_id: Technique identifier (e.g. "chiaroscuro").

    Returns:
        Technique or None if not found.
    """
    _load_corpus()
    return _techniques.get(technique_id)


def get_all_techniques(category: Optional[str] = None) -> List[Technique]:
    """Get all techniques, optionally filtered by category.

    Args:
        category: Optional category filter.

    Returns:
        List of Technique objects.
    """
    _load_corpus()
    if category:
        return [t for t in _techniques.values() if t.category == category]
    return list(_techniques.values())


def suggest_transitions(
    scene_a_mood: str,
    scene_b_mood: str,
    top_k: int = 5,
) -> List[TransitionSuggestion]:
    """Suggest transition techniques between two scenes based on mood.

    Analyzes the mood contrast between scenes to recommend appropriate
    transition techniques from the corpus.

    Args:
        scene_a_mood: Mood of the outgoing scene.
        scene_b_mood: Mood of the incoming scene.
        top_k: Maximum suggestions to return.

    Returns:
        Ranked list of TransitionSuggestion.
    """
    _load_corpus()
    suggestions: List[TransitionSuggestion] = []

    mood_a = scene_a_mood.lower().strip()
    mood_b = scene_b_mood.lower().strip()

    # Determine transition character based on mood similarity
    transition_character = _classify_transition_character(mood_a, mood_b)

    # Get candidate transition technique IDs from transition_mood_map
    candidate_ids: List[str] = []
    for character in transition_character:
        candidate_ids.extend(_transition_mood_map.get(character, []))

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_ids: List[str] = []
    for tid in candidate_ids:
        if tid not in seen:
            seen.add(tid)
            unique_ids.append(tid)

    for idx, tid in enumerate(unique_ids):
        technique = _techniques.get(tid)
        if technique is None:
            continue

        score = 1.0 - (idx * 0.08)
        reasoning = _build_transition_reasoning(
            technique, mood_a, mood_b, transition_character,
        )

        suggestions.append(TransitionSuggestion(
            technique=technique,
            score=max(score, 0.1),
            reasoning_ko=reasoning,
        ))

    suggestions.sort(key=lambda s: s.score, reverse=True)
    return suggestions[:top_k]


# =============================================================================
# Internal Helpers
# =============================================================================

def _keyword_score(query: str, technique: Technique) -> float:
    """Simple keyword matching score."""
    score = 0.0
    query_words = query.split()

    # Check best_for tags
    for word in query_words:
        for tag in technique.best_for:
            if word in tag or tag in word:
                score += 0.4

    # Check description_ko
    if query in technique.description_ko:
        score += 0.3

    # Check visual_effect_ko
    if query in technique.visual_effect_ko:
        score += 0.2

    # Check name fields
    if query in technique.name_ko or query in technique.name_en.lower():
        score += 0.5

    return min(score, 0.95)


_MOOD_GROUPS = {
    "calm": {"serenity", "contemplation", "romance", "nostalgia"},
    "intense": {"tension", "chaos", "horror", "energy"},
    "dark": {"mystery", "horror", "isolation"},
    "bright": {"romance", "nostalgia", "epic", "energy"},
}


def _classify_transition_character(
    mood_a: str, mood_b: str,
) -> List[str]:
    """Classify the transition character based on mood shift."""

    # Same mood group → smooth/continuous
    for _group_name, moods in _MOOD_GROUPS.items():
        if mood_a in moods and mood_b in moods:
            return ["smooth", "continuous"]

    # Calm → intense (or vice versa) → dramatic
    calm = _MOOD_GROUPS["calm"]
    intense = _MOOD_GROUPS["intense"]

    if (mood_a in calm and mood_b in intense) or (mood_a in intense and mood_b in calm):
        return ["dramatic", "energetic"]

    # Dark → bright (or vice versa) → dramatic/disruptive
    dark = _MOOD_GROUPS["dark"]
    bright = _MOOD_GROUPS["bright"]

    if (mood_a in dark and mood_b in bright) or (mood_a in bright and mood_b in dark):
        return ["dramatic", "disruptive"]

    # Default: smooth
    return ["smooth", "dramatic"]


def _build_transition_reasoning(
    technique: Technique,
    mood_a: str,
    mood_b: str,
    characters: List[str],
) -> str:
    """Build Korean reasoning text for a transition suggestion."""
    char_ko = {
        "smooth": "부드러운",
        "energetic": "에너지 넘치는",
        "dramatic": "극적인",
        "continuous": "연속적인",
        "disruptive": "파괴적인",
    }
    char_desc = ", ".join(char_ko.get(c, c) for c in characters)

    return (
        f"'{mood_a}' → '{mood_b}' 전환에 {char_desc} 특성의 "
        f"'{technique.name_ko}' 기법 추천. {technique.visual_effect_ko}."
    )
