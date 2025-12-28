import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.storyboard_utils import build_shot_id, normalize_storyboard_cards


def test_build_shot_id_with_sequence():
    shot_id = build_shot_id("c2", 2, sequence_id="seq-03")
    assert shot_id == "shot-03-02"


def test_normalize_storyboard_cards_populates_fields():
    cards = [{"card_id": "c1", "shot": "wide shot"}]
    normalized = normalize_storyboard_cards(cards)
    card = normalized[0]
    assert card["shot_id"] == "shot-01"
    assert card["shot_type"] == "wide"
    assert card["composition"] == "wide shot"
    assert card["dominant_color"] == "#333333"
    assert card["accent_color"] == "#555555"
