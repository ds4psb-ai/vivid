import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.template_seeding import _derive_persona_synapse_params


def test_derive_persona_synapse_params_overrides_capsule_params():
    record = SimpleNamespace(
        guide_type="persona",
        pacing={"tempo": "fast"},
        editing_rhythm=None,
        persona_profile=None,
        synapse_logic=None,
        color_palette={"bias": "cool"},
        confidence=0.82,
        cluster_confidence=None,
        signature_motifs=[],
    )

    overrides = _derive_persona_synapse_params(
        [record],
        "auteur.bong-joon-ho",
        {"style_intensity": 0.7},
    )

    assert overrides["pacing"] == "fast"
    assert overrides["color_bias"] == "cool"
    assert overrides["tension_bias"] == 0.82
