"""Shot-level pattern extraction for Original-IP Foundry."""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from app.features.original_ip_foundry.qdrant_pattern_store import QdrantPatternAtomStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PatternKey:
    camera_angle: str
    camera_movement: str
    shot_size: str
    emotion_tone: str
    transition: str

    def to_atom_id(self) -> str:
        return "::".join(
            [
                self.camera_angle,
                self.camera_movement,
                self.shot_size,
                self.emotion_tone,
                self.transition,
            ]
        )


class PatternExtractionService:
    """Extract and index pattern atoms from shot sequences."""

    def __init__(self, qdrant_store: Optional["QdrantPatternAtomStore"] = None):
        self._atoms_by_project: Dict[str, List[dict]] = defaultdict(list)
        self._atoms_by_project_scene: Dict[tuple[str, str], List[dict]] = {}
        self._qdrant_store = qdrant_store

    def extract(
        self,
        *,
        project_id: str,
        scene_id: str,
        shots: List[dict],
    ) -> dict:
        counter: Counter[PatternKey] = Counter()
        transition_counter: Counter[str] = Counter()

        for index, shot in enumerate(shots):
            transition = shot.get("transition_to_next") or "cut"
            key = PatternKey(
                camera_angle=str(shot.get("camera_angle") or "eye_level").lower(),
                camera_movement=str(shot.get("camera_movement") or "static").lower(),
                shot_size=str(shot.get("shot_size") or "medium").lower(),
                emotion_tone=str(shot.get("emotion_tone") or "neutral").lower(),
                transition=str(transition).lower(),
            )
            counter[key] += 1

            if index < len(shots) - 1:
                next_size = str(shots[index + 1].get("shot_size") or "medium").lower()
                transition_key = f"{key.shot_size}->{next_size}:{key.transition}"
                transition_counter[transition_key] += 1

        total = max(len(shots), 1)
        atoms = []
        for key, count in counter.most_common():
            confidence = min(0.95, round(0.45 + (count / total) * 0.6, 4))
            atoms.append(
                {
                    "atom_id": key.to_atom_id(),
                    "camera_angle": key.camera_angle,
                    "camera_movement": key.camera_movement,
                    "shot_size": key.shot_size,
                    "emotion_tone": key.emotion_tone,
                    "transition": key.transition,
                    "frequency": count,
                    "confidence": confidence,
                }
            )

        transition_rules = [
            {"rule": rule, "frequency": freq}
            for rule, freq in transition_counter.most_common()
        ]

        result = {
            "project_id": project_id,
            "scene_id": scene_id,
            "pattern_atoms": atoms,
            "transition_rules": transition_rules,
            "total_shots": len(shots),
        }
        self._atoms_by_project[project_id].extend(atoms)
        self._atoms_by_project_scene[(project_id, scene_id)] = atoms

        if self._qdrant_store and atoms:
            try:
                self._qdrant_store.upsert_batch(
                    project_id=project_id, scene_id=scene_id, atoms=atoms,
                )
            except Exception as e:
                logger.warning(f"[PatternExtraction] Qdrant persistence failed (non-fatal): {e}")

        return result

    def search_atoms(self, project_id: str, query: str, limit: int = 5) -> List[dict]:
        # Try Qdrant first if available
        if self._qdrant_store:
            try:
                qdrant_results = self._qdrant_store.search_atoms(
                    project_id=project_id, query=query, limit=limit,
                )
                if qdrant_results:
                    return qdrant_results
            except Exception as e:
                logger.warning(f"[PatternExtraction] Qdrant search failed, falling back to in-memory: {e}")

        # In-memory fallback
        haystack = self._atoms_by_project.get(project_id, [])
        if not haystack:
            return []

        query_terms = [term.lower() for term in query.split() if term.strip()]
        scored: list[tuple[float, dict]] = []
        for atom in haystack:
            text = " ".join(
                [
                    atom.get("atom_id", ""),
                    atom.get("camera_angle", ""),
                    atom.get("camera_movement", ""),
                    atom.get("shot_size", ""),
                    atom.get("emotion_tone", ""),
                ]
            ).lower()
            if query_terms:
                score = sum(1 for term in query_terms if term in text) / len(query_terms)
            else:
                score = 0.0
            if score > 0:
                scored.append((score + atom.get("confidence", 0), atom))

        if not scored:
            return haystack[:limit]

        scored.sort(key=lambda item: item[0], reverse=True)
        return [atom for _, atom in scored[:limit]]

