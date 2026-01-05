import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.spec_engine import _generate_shot_contracts


def test_generate_shot_contracts_uses_sequence_id_for_shot_id():
    inputs = {"sequence_id": "seq-02", "scene_id": "scene-01"}
    storyboard = [{"card_id": "c1", "composition": "wide shot"}]
    contracts = _generate_shot_contracts(inputs, storyboard)
    assert contracts[0]["shot_id"] == "shot-02-01"
    assert contracts[0]["sequence_id"] == "seq-02"
