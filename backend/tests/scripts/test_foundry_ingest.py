"""Tests for foundry ingestion scripts."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BACKEND_DIR / "data" / "foundry" / "seed_shot_corpus.json"
SHOT_SCRIPT = BACKEND_DIR / "scripts" / "foundry_ingest_shot_corpus.py"
ATOM_SCRIPT = BACKEND_DIR / "scripts" / "foundry_ingest_pattern_atoms.py"


# ── Seed data validation ──────────────────────────────────────────────


class TestSeedDataValidation:
    """Validate seed_shot_corpus.json integrity."""

    @pytest.fixture(scope="class")
    def shots(self) -> list[dict]:
        assert DATA_PATH.exists(), f"Seed data not found: {DATA_PATH}"
        with open(DATA_PATH) as f:
            return json.load(f)

    def test_total_count(self, shots):
        assert len(shots) == 250

    def test_director_distribution(self, shots):
        from collections import Counter
        dist = Counter(s["director"] for s in shots)
        expected_directors = {"kubrick", "bong", "tarantino", "nolan", "wong_kar_wai"}
        assert set(dist.keys()) == expected_directors
        for director in expected_directors:
            assert dist[director] == 50, f"{director} has {dist[director]} shots, expected 50"

    def test_required_fields_present(self, shots):
        required = {"shot_id", "shot_size", "camera_angle", "camera_movement", "emotion_tone", "transition_to_next", "director"}
        for i, shot in enumerate(shots):
            missing = required - set(shot.keys())
            assert not missing, f"Shot {i} ({shot.get('shot_id', '?')}) missing: {missing}"

    def test_shot_ids_unique(self, shots):
        ids = [s["shot_id"] for s in shots]
        assert len(ids) == len(set(ids)), "Duplicate shot_ids found"

    def test_valid_enum_values(self, shots):
        valid_sizes = {"extreme_wide", "wide", "medium_wide", "medium", "medium_close_up", "close_up", "extreme_close_up"}
        valid_angles = {"eye_level", "low_angle", "high_angle", "dutch_angle", "birds_eye", "worms_eye"}
        valid_movements = {"static", "dolly", "tracking", "handheld", "crane", "whip_pan", "steadicam"}
        valid_emotions = {"neutral", "tension", "melancholy", "joy", "fear", "rage", "intimacy", "isolation", "power", "awe"}
        valid_transitions = {"cut", "dissolve", "match_cut", "fade", "wipe", "jump_cut"}

        for i, s in enumerate(shots):
            assert s["shot_size"] in valid_sizes, f"Shot {i}: bad shot_size '{s['shot_size']}'"
            assert s["camera_angle"] in valid_angles, f"Shot {i}: bad camera_angle '{s['camera_angle']}'"
            assert s["camera_movement"] in valid_movements, f"Shot {i}: bad camera_movement '{s['camera_movement']}'"
            assert s["emotion_tone"] in valid_emotions, f"Shot {i}: bad emotion_tone '{s['emotion_tone']}'"
            assert s["transition_to_next"] in valid_transitions, f"Shot {i}: bad transition '{s['transition_to_next']}'"

    def test_shot_id_prefix_matches_director(self, shots):
        for s in shots:
            expected_prefix = f"ref_{s['director']}_"
            assert s["shot_id"].startswith(expected_prefix), (
                f"Shot {s['shot_id']} doesn't match director {s['director']}"
            )

    def test_duration_positive(self, shots):
        for s in shots:
            assert s.get("duration_sec", 1.0) > 0, f"Shot {s['shot_id']} has non-positive duration"


# ── Dry-run mode ───────────────────────────────────────────────────────


class TestShotCorpusDryRun:
    """Test shot corpus ingestion script in dry-run mode."""

    def test_dry_run_succeeds(self):
        result = subprocess.run(
            [sys.executable, str(SHOT_SCRIPT), "--dry-run", "--data-path", str(DATA_PATH)],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
        )
        assert result.returncode == 0, f"Dry run failed: {result.stderr}"
        assert "DRY RUN" in result.stdout
        assert "250 shots validated OK" in result.stdout

    def test_dry_run_shows_distribution(self):
        result = subprocess.run(
            [sys.executable, str(SHOT_SCRIPT), "--dry-run", "--data-path", str(DATA_PATH)],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
        )
        assert "kubrick: 50" in result.stdout
        assert "bong: 50" in result.stdout

    def test_missing_file_exits_with_error(self):
        result = subprocess.run(
            [sys.executable, str(SHOT_SCRIPT), "--dry-run", "--data-path", "nonexistent.json"],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
        )
        assert result.returncode != 0
        assert "ERROR" in result.stdout


class TestPatternAtomsDryRun:
    """Test pattern atoms ingestion script in dry-run mode."""

    def test_dry_run_succeeds(self):
        result = subprocess.run(
            [sys.executable, str(ATOM_SCRIPT), "--dry-run", "--data-path", str(DATA_PATH)],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
        )
        assert result.returncode == 0, f"Dry run failed: {result.stderr}"
        assert "DRY RUN" in result.stdout
        assert "atoms extracted" in result.stdout

    def test_dry_run_extracts_atoms_for_all_directors(self):
        result = subprocess.run(
            [sys.executable, str(ATOM_SCRIPT), "--dry-run", "--data-path", str(DATA_PATH)],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
        )
        for director in ["bong", "kubrick", "nolan", "tarantino", "wong_kar_wai"]:
            assert director in result.stdout, f"Director {director} not in output"


# ── Qdrant ingestion (mocked) ─────────────────────────────────────────


class TestShotCorpusIngestion:
    """Test shot corpus Qdrant ingestion logic."""

    def test_ingestion_point_construction(self):
        """Verify point construction logic produces correct count and vector dims."""
        import hashlib

        with open(DATA_PATH) as f:
            shots = json.load(f)

        points = []
        for shot in shots:
            text = f"{shot['shot_size']} {shot['camera_angle']} {shot['camera_movement']} {shot['emotion_tone']} {shot['transition_to_next']}"
            h = hashlib.sha384(text.encode()).digest()
            vector = [((b - 128) / 128.0) for b in h]
            point_id = hashlib.md5(shot["shot_id"].encode()).hexdigest()
            points.append({"id": point_id, "vector": vector, "payload": shot})

        assert len(points) == 250
        # sha384 = 48 bytes
        assert len(points[0]["vector"]) == 48

    def test_point_ids_unique(self):
        """Each shot_id should produce a unique point_id."""
        import hashlib

        with open(DATA_PATH) as f:
            shots = json.load(f)

        point_ids = [hashlib.md5(s["shot_id"].encode()).hexdigest() for s in shots]
        assert len(point_ids) == len(set(point_ids))

    def test_hash_vectors_deterministic(self):
        """Same input always produces same vector."""
        import hashlib
        text = "wide low_angle dolly tension match_cut"
        h1 = hashlib.sha384(text.encode()).digest()
        h2 = hashlib.sha384(text.encode()).digest()
        v1 = [((b - 128) / 128.0) for b in h1]
        v2 = [((b - 128) / 128.0) for b in h2]
        assert v1 == v2


# ── Pattern extraction integration ────────────────────────────────────


class TestPatternExtractionFromCorpus:
    """Test PatternExtractionService with actual corpus data."""

    def test_extract_kubrick_patterns(self):
        from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService

        with open(DATA_PATH) as f:
            shots = json.load(f)

        kubrick_shots = [s for s in shots if s["director"] == "kubrick"]
        service = PatternExtractionService(qdrant_store=None)
        result = service.extract(
            project_id="seed_kubrick",
            scene_id="corpus_kubrick",
            shots=kubrick_shots,
        )

        assert result["project_id"] == "seed_kubrick"
        assert result["total_shots"] == 50
        assert len(result["pattern_atoms"]) > 0
        assert len(result["transition_rules"]) > 0

        # Kubrick signature: should have atoms with dolly/steadicam movements
        movements = {a["camera_movement"] for a in result["pattern_atoms"]}
        assert "dolly" in movements or "steadicam" in movements

    def test_extract_all_directors(self):
        from collections import defaultdict
        from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService

        with open(DATA_PATH) as f:
            shots = json.load(f)

        by_director = defaultdict(list)
        for s in shots:
            by_director[s["director"]].append(s)

        service = PatternExtractionService(qdrant_store=None)
        for director, director_shots in by_director.items():
            result = service.extract(
                project_id=f"seed_{director}",
                scene_id=f"corpus_{director}",
                shots=director_shots,
            )
            assert result["total_shots"] == 50
            assert len(result["pattern_atoms"]) > 0, f"{director} has no atoms"
