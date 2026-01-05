import pytest
from pydantic import ValidationError

from app.routers.ingest import VideoStructuredRequest


def _base_payload() -> dict:
    return {
        "segment_id": "seg-demo-001",
        "source_id": "auteur-bong-1999-barking-dogs",
        "work_id": "work-demo-001",
        "scene_id": "scene-demo-001",
        "shot_id": "shot-demo-001",
        "time_start": "00:00:10.000",
        "time_end": "00:00:12.000",
        "prompt_version": "gemini-video-v1",
        "model_version": "gemini-3-pro-2025-12",
    }


def test_video_structured_valid_payload() -> None:
    payload = _base_payload()
    record = VideoStructuredRequest(**payload)
    assert record.segment_id == payload["segment_id"]


def test_video_structured_invalid_timecode_format() -> None:
    payload = _base_payload()
    payload["time_start"] = "00:00:1.000"
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_timecode_order() -> None:
    payload = _base_payload()
    payload["time_end"] = "00:00:09.000"
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_prompt_version_allowlist() -> None:
    payload = _base_payload()
    payload["prompt_version"] = "invalid-version"
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_visual_schema_unknown_key() -> None:
    payload = _base_payload()
    payload["visual_schema_json"] = {"unknown_key": "value"}
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_audio_schema_type() -> None:
    payload = _base_payload()
    payload["audio_schema_json"] = "not-an-object"
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_keyframes_empty_list() -> None:
    payload = _base_payload()
    payload["keyframes"] = []
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_motifs_empty_list() -> None:
    payload = _base_payload()
    payload["motifs"] = []
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_evidence_refs_empty_list() -> None:
    payload = _base_payload()
    payload["evidence_refs"] = []
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_list_values_trimmed() -> None:
    payload = _base_payload()
    payload["keyframes"] = [" kf_001 "]
    payload["motifs"] = [" stairs "]
    payload["evidence_refs"] = [" source:00:00:10-00:00:12 "]
    record = VideoStructuredRequest(**payload)
    assert record.keyframes == ["kf_001"]
    assert record.motifs == ["stairs"]
    assert record.evidence_refs == ["source:00:00:10-00:00:12"]


def test_video_structured_keyframes_format() -> None:
    payload = _base_payload()
    payload["keyframes"] = ["bad id"]
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)


def test_video_structured_evidence_refs_format() -> None:
    payload = _base_payload()
    payload["evidence_refs"] = ["00:00:10-00:00:12"]
    with pytest.raises(ValidationError):
        VideoStructuredRequest(**payload)
