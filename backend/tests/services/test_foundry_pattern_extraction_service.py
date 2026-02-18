from unittest.mock import MagicMock

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


def _sample_shots():
    return [
        {"shot_id": "s1", "camera_angle": "low_angle", "camera_movement": "tracking",
         "shot_size": "close_up", "emotion_tone": "anxiety", "transition_to_next": "cut"},
    ]


def test_extract_calls_qdrant_store_when_injected():
    mock_store = MagicMock()
    mock_store.upsert_batch.return_value = ["id-1"]
    service = PatternExtractionService(qdrant_store=mock_store)

    service.extract(project_id="p1", scene_id="s1", shots=_sample_shots())

    mock_store.upsert_batch.assert_called_once()
    call_kwargs = mock_store.upsert_batch.call_args.kwargs
    assert call_kwargs["project_id"] == "p1"
    assert call_kwargs["scene_id"] == "s1"
    assert len(call_kwargs["atoms"]) >= 1


def test_extract_without_qdrant_store_still_works():
    service = PatternExtractionService(qdrant_store=None)
    result = service.extract(project_id="p1", scene_id="s1", shots=_sample_shots())

    assert result["total_shots"] == 1
    assert len(result["pattern_atoms"]) >= 1


def test_search_atoms_prefers_qdrant_results():
    mock_store = MagicMock()
    mock_store.search_atoms.return_value = [
        {"atom_id": "qdrant_result", "camera_angle": "low_angle", "confidence": 0.9}
    ]
    service = PatternExtractionService(qdrant_store=mock_store)
    service.extract(project_id="p1", scene_id="s1", shots=_sample_shots())

    results = service.search_atoms("p1", "low angle")
    assert results[0]["atom_id"] == "qdrant_result"


def test_search_atoms_falls_back_on_qdrant_failure():
    mock_store = MagicMock()
    mock_store.search_atoms.side_effect = Exception("connection lost")
    mock_store.upsert_batch.return_value = []
    service = PatternExtractionService(qdrant_store=mock_store)
    service.extract(project_id="p1", scene_id="s1", shots=_sample_shots())

    results = service.search_atoms("p1", "low_angle tracking")
    assert len(results) >= 1
    assert results[0]["camera_angle"] == "low_angle"

