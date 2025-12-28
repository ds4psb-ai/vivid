import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.narrative_utils import normalize_story_beats, normalize_storyboard_cards


def test_normalize_story_beats_fills_defaults():
    beats = [{"beat_id": "b10", "note": "Introduce the world", "tension": "weird"}]
    normalized = normalize_story_beats(beats)
    assert normalized[0]["beat_id"] == "b10"
    assert normalized[0]["summary"] == "Introduce the world"
    assert normalized[0]["tension"] == "medium"


def test_normalize_story_beats_from_string():
    normalized = normalize_story_beats(["A tense reveal"])
    assert normalized[0]["beat_id"] == "b1"
    assert normalized[0]["summary"] == "A tense reveal"
    assert normalized[0]["tension"] == "medium"


def test_normalize_storyboard_cards_defaults():
    cards = [{"composition": "wide shot", "note": "Establishing"}]
    normalized = normalize_storyboard_cards(cards)
    assert normalized[0]["card_id"] == "c1"
    assert normalized[0]["shot"] == "wide shot"
    assert normalized[0]["note"] == "Establishing"


def test_normalize_storyboard_cards_from_string():
    normalized = normalize_storyboard_cards(["Hero enters frame"])
    assert normalized[0]["card_id"] == "c1"
    assert normalized[0]["note"] == "Hero enters frame"
