import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.template_learning import (
    compute_reward,
    extract_capsule_params,
    extract_evidence_refs,
    extract_template_origin,
)


def test_extract_template_origin_prefers_origin_block():
    graph = {
        "meta": {
            "template_id": "legacy",
            "template_version": 1,
            "template_origin": {
                "template_id": "origin-id",
                "template_version": 2,
                "template_slug": "origin-slug",
            },
        }
    }
    template_id, template_version, template_slug = extract_template_origin(graph)
    assert template_id == "origin-id"
    assert template_version == 2
    assert template_slug == "origin-slug"


def test_extract_evidence_refs_filters_prefixes():
    graph = {
        "meta": {
            "evidence_refs": ["sheet:row-1", "db:segment-2", "http://bad", "", 3]
        }
    }
    refs = extract_evidence_refs(graph)
    assert refs == ["sheet:row-1", "db:segment-2"]


def test_extract_capsule_params_collects_capsules():
    graph = {
        "nodes": [
            {"id": "n1", "type": "input", "data": {}},
            {
                "id": "n2",
                "type": "capsule",
                "data": {"capsuleId": "auteur.bong", "capsuleVersion": "1.0.0", "params": {"pacing": "fast"}},
            },
        ]
    }
    capsules = extract_capsule_params(graph)
    assert len(capsules) == 1
    assert capsules[0]["capsule_id"] == "auteur.bong"
    assert capsules[0]["params"]["pacing"] == "fast"


def test_compute_reward_returns_breakdown():
    reward = compute_reward(
        feedback_shots=[{"shot_id": "shot-1", "rating": 4}],
        evidence_refs=["sheet:row-1", "db:segment-2"],
        credit_cost=20,
        shot_count=2,
    )
    assert 0.0 <= reward["score"] <= 1.0
    assert reward["components"]["rating_score"] > 0
    assert reward["components"]["evidence_score"] > 0
