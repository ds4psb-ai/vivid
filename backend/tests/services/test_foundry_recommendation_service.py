from app.features.original_ip_foundry.recommendation_service import FoundryRecommendationService
from app.features.original_ip_foundry.rights_service import FoundryRightsService


def test_recommendation_blocks_when_rights_fail():
    service = FoundryRecommendationService(FoundryRightsService())
    result = service.recommend(
        scene_context={
            "scene_id": "scene-10",
            "characters": ["hero"],
            "location": "warehouse",
            "desired_camera_rhythm": "dynamic",
            "intent_tags": ["power"],
        },
        candidates=[
            {
                "candidate_id": "cand-1",
                "title": "Blocked candidate",
                "shots": [
                    {
                        "shot_id": "shot-1",
                        "characters": ["hero"],
                        "location": "warehouse",
                        "camera_movement": "tracking",
                        "emotion_tone": "neutral",
                    }
                ],
                "rights_assets": [
                    {
                        "asset_id": "asset-a",
                        "source_license": "cc-by",
                        "derivative_allowed": False,
                        "allowed_actions": ["reference"],
                    }
                ],
                "pattern_tags": ["power"],
                "mise_en_scene_score": 0.8,
                "story_intent_fit": 0.8,
                "director_style_fit": 0.8,
                "execution_feasibility": 0.8,
                "clone_risk": 0.2,
            }
        ],
        rights_action="remix",
        continuity_floor=0.6,
    )

    top = result["ranked"][0]
    assert top["decision"] == "block"
    assert top["rights_decision"] == "block"
    assert "RIGHTS_BLOCKED" in top["reason_codes"]


def test_recommendation_holds_when_continuity_below_gate():
    service = FoundryRecommendationService(FoundryRightsService())
    result = service.recommend(
        scene_context={
            "scene_id": "scene-11",
            "characters": ["hero", "villain"],
            "location": "subway",
            "desired_camera_rhythm": "steady",
            "intent_tags": ["isolation"],
        },
        candidates=[
            {
                "candidate_id": "cand-2",
                "title": "Low continuity",
                "shots": [
                    {
                        "shot_id": "shot-1",
                        "characters": ["extra"],
                        "location": "desert",
                        "camera_movement": "handheld",
                        "emotion_tone": "panic",
                    }
                ],
                "rights_assets": [],
                "pattern_tags": ["power"],
                "mise_en_scene_score": 0.6,
                "story_intent_fit": 0.6,
                "director_style_fit": 0.6,
                "execution_feasibility": 0.6,
                "clone_risk": 0.1,
            }
        ],
        rights_action="reference",
        continuity_floor=0.7,
    )

    top = result["ranked"][0]
    assert top["decision"] == "hold"
    assert top["continuity_score"] < 0.7
    assert "CONTINUITY_BELOW_GATE" in top["reason_codes"]

