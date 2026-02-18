"""Near-duplicate detection for Foundry scene submissions."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import xxhash
    _HAS_XXHASH = True
except ImportError:
    import hashlib
    _HAS_XXHASH = False
    logger.warning("[NearDuplicate] xxhash not available, falling back to sha256")


class NearDuplicateService:
    """Two-tier duplicate detection: exact hash + semantic similarity."""

    COSINE_BLOCK_THRESHOLD = 0.92
    COSINE_REVIEW_THRESHOLD = 0.85
    MAX_HASH_REGISTRY = 50_000

    def __init__(self, qdrant_pattern_store=None):
        self._qdrant_store = qdrant_pattern_store
        self._hash_registry: dict[str, str] = {}  # hash -> original_id

    def _evict_oldest_hash(self) -> None:
        """Evict oldest hash entry if at capacity."""
        if len(self._hash_registry) >= self.MAX_HASH_REGISTRY:
            oldest_key = next(iter(self._hash_registry))
            del self._hash_registry[oldest_key]

    def compute_content_hash(self, shots: list[dict]) -> str:
        """Compute deterministic content hash from normalized shot sequence."""
        normalized = []
        for shot in shots:
            key = "|".join([
                str(shot.get("camera_angle", "")),
                str(shot.get("camera_movement", "")),
                str(shot.get("shot_size", "")),
                str(shot.get("emotion_tone", "")),
                str(shot.get("transition_to_next", "")),
            ])
            normalized.append(key)
        normalized.sort()
        content = "::".join(normalized)
        if _HAS_XXHASH:
            return xxhash.xxh64(content.encode("utf-8")).hexdigest()
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def check_duplicate(
        self,
        *,
        project_id: str,
        scene_id: str,
        shots: list[dict],
    ) -> dict:
        """Check for near-duplicate content. Returns decision dict."""
        content_hash = self.compute_content_hash(shots)
        reason_codes: list[str] = []
        similarity: Optional[float] = None

        # Tier 1: Exact hash match
        if content_hash in self._hash_registry:
            original_id = self._hash_registry[content_hash]
            return {
                "decision": "block",
                "reason_codes": ["EXACT_HASH_MATCH"],
                "similarity": 1.0,
                "content_hash": content_hash,
                "original_id": original_id,
            }

        # Tier 2: Semantic similarity via Qdrant
        if self._qdrant_store:
            try:
                query_text = " ".join(
                    f"{s.get('camera_angle', '')} {s.get('camera_movement', '')} "
                    f"{s.get('shot_size', '')} {s.get('emotion_tone', '')}"
                    for s in shots[:10]
                )
                results = self._qdrant_store.search_atoms(
                    project_id=project_id, query=query_text, limit=1,
                )
                if results:
                    top_confidence = results[0].get("confidence", 0.0)
                    similarity = top_confidence
                    if top_confidence >= self.COSINE_BLOCK_THRESHOLD:
                        reason_codes.append("SEMANTIC_NEAR_DUPLICATE")
                        self._evict_oldest_hash()
                        self._hash_registry[content_hash] = f"{project_id}:{scene_id}"
                        return {
                            "decision": "block",
                            "reason_codes": reason_codes,
                            "similarity": similarity,
                            "content_hash": content_hash,
                        }
                    if top_confidence >= self.COSINE_REVIEW_THRESHOLD:
                        reason_codes.append("SEMANTIC_HIGH_SIMILARITY")
                        self._evict_oldest_hash()
                        self._hash_registry[content_hash] = f"{project_id}:{scene_id}"
                        return {
                            "decision": "review",
                            "reason_codes": reason_codes,
                            "similarity": similarity,
                            "content_hash": content_hash,
                        }
            except Exception as e:
                logger.warning(f"[NearDuplicate] Semantic check failed: {e}")

        # Register hash and allow
        self._evict_oldest_hash()
        self._hash_registry[content_hash] = f"{project_id}:{scene_id}"
        return {
            "decision": "allow",
            "reason_codes": reason_codes,
            "similarity": similarity,
            "content_hash": content_hash,
        }
