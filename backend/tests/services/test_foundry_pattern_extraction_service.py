from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService


def test_extract_generates_pattern_atoms_and_transition_rules():
    service = PatternExtractionService()

    result = service.extract(
        project_id="p1",
        scene_id="s1",
        shots=[
            {
                "shot_id": "shot-1",
                "camera_angle": "low_angle",
                "camera_movement": "tracking",
                "shot_size": "medium",
                "emotion_tone": "anxiety",
                "transition_to_next": "cut",
            },
            {
                "shot_id": "shot-2",
                "camera_angle": "low_angle",
                "camera_movement": "tracking",
                "shot_size": "close_up",
                "emotion_tone": "anxiety",
                "transition_to_next": "cut",
            },
        ],
    )

    assert result["project_id"] == "p1"
    assert result["scene_id"] == "s1"
    assert result["total_shots"] == 2
    assert len(result["pattern_atoms"]) >= 1
    assert result["pattern_atoms"][0]["confidence"] > 0
    assert len(result["transition_rules"]) == 1


def test_search_atoms_returns_ranked_results():
    service = PatternExtractionService()
    service.extract(
        project_id="p2",
        scene_id="s2",
        shots=[
            {
                "shot_id": "shot-1",
                "camera_angle": "high_angle",
                "camera_movement": "handheld",
                "shot_size": "close_up",
                "emotion_tone": "panic",
                "transition_to_next": "match_cut",
            }
        ],
    )
    items = service.search_atoms("p2", "handheld panic", limit=3)
    assert len(items) == 1
    assert items[0]["camera_movement"] == "handheld"

