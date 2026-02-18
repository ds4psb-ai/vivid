"""Foundry-dedicated Qdrant collections initialization."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

FOUNDRY_COLLECTIONS = {
    "foundry_shot_corpus": {"vector_size": 384, "description": "Reference shot DB"},
    "foundry_pattern_atoms": {"vector_size": 384, "description": "Cinematic pattern atoms"},
    "foundry_transition_rules": {"vector_size": 384, "description": "Scene transition rules"},
    "foundry_rights_constraints": {"vector_size": 384, "description": "Rights metadata mirror"},
    "foundry_director_memory": {"vector_size": 384, "description": "OpenClaw director notes"},
}

# Payload indexes common to all collections
COMMON_PAYLOAD_INDEXES = ["tenant_id", "project_id", "scene_id"]

# Extra indexes per collection
EXTRA_PAYLOAD_INDEXES = {
    "foundry_pattern_atoms": ["pattern_type", "source_license"],
    "foundry_rights_constraints": ["license_type", "derivative_allowed"],
}


async def ensure_all_foundry_collections() -> None:
    """Initialize all Foundry Qdrant collections.

    Non-fatal on Qdrant unavailability -- caller should catch exceptions.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qdrant_models
        from app.config import settings

        qdrant_api_key: Optional[str] = (
            settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None
        )
        client = QdrantClient(url=settings.QDRANT_URL, api_key=qdrant_api_key, timeout=10)

        existing = {c.name for c in client.get_collections().collections}

        for name, config in FOUNDRY_COLLECTIONS.items():
            if name not in existing:
                client.create_collection(
                    collection_name=name,
                    vectors_config=qdrant_models.VectorParams(
                        size=config["vector_size"],
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
                logger.info(f"[Foundry] Created collection: {name}")
            else:
                logger.debug(f"[Foundry] Collection exists: {name}")

            # Create payload indexes
            indexes = COMMON_PAYLOAD_INDEXES + EXTRA_PAYLOAD_INDEXES.get(name, [])
            for field in indexes:
                try:
                    client.create_payload_index(
                        collection_name=name,
                        field_name=field,
                        field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                    )
                except Exception:
                    pass  # index may already exist

        logger.info(f"[Foundry] All {len(FOUNDRY_COLLECTIONS)} collections initialized")
    except Exception as e:
        logger.warning(f"[Foundry] Qdrant collection init failed (non-fatal): {e}")
        raise
