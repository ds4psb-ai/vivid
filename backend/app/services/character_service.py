"""Character Consistency Service.

Business logic for StoryMem-based character consistency system.

Features:
- Character CRUD operations
- Embedding extraction (Face + CLIP + Style)
- Memory bank management (StoryMem algorithm)
- Platform synchronization (Veo Ingredients, Kling Elements)
- Similarity search with CoFE fusion

2026 Best Practices:
- ArcFace R100: Identity-preserving face embeddings (512D)
- CLIP ViT-L/14: Visual similarity embeddings (768D)
- HPSv3: Aesthetic quality prediction
- Qdrant Named Vectors for multi-modal search
- CoFE multi-expert fusion for character matching

References:
- StoryMem Paper: arXiv:2512.19539
- Arc2Face: arXiv:2403.11641
- CoFE: arXiv:2508.09476
- DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_character import Character, CharacterAppearance
from app.schemas.character_schemas import (
    CharacterCreateRequest,
    CharacterResponse,
    CharacterSummaryResponse,
    CharacterSimilarity,
    CharacterUpdateRequest,
    MemoryKeyframe,
    MemoryBankResponse,
    PlatformRef,
    PlatformSyncResponse,
    PlatformType,
    SourceImage,
    KeyframeSelectionConfig,
)
from app.services.character_embedding_service import (
    CharacterEmbeddingService,
    CharacterEmbedding,
    get_character_embedding_service,
)
from app.services.embedding_extractor import (
    EmbeddingResult,
    get_embedding_extractor,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Qdrant collection for character embeddings
QDRANT_COLLECTION = "character_embeddings"

# Memory bank limits
MAX_LONG_TERM_KEYFRAMES = 10
MAX_SLIDING_WINDOW_KEYFRAMES = 20

# Reference image limits (2026 Best Practices - Gemini 3 Pro Image)
MAX_REFERENCE_IMAGES = 14  # Gemini 3 Pro Image supports up to 14 reference images
RECOMMENDED_REFERENCE_IMAGES = 10  # 5-10 recommended for best results
MAX_CHARACTERS_PER_VIDEO = 5  # Supports up to 5 people consistency

# Embedding dimensions
FACE_EMBED_DIM = 512   # ArcFace
CLIP_EMBED_DIM = 768   # CLIP ViT-L/14
STYLE_EMBED_DIM = 768  # Style encoder


# ============================================================================
# Character CRUD
# ============================================================================

async def create_character(
    db: AsyncSession,
    user_id: str,
    request: CharacterCreateRequest,
) -> Character:
    """Create a new character with initial reference image.

    Workflow:
    1. Create character record in PostgreSQL
    2. If reference image provided:
       - Extract face embedding (ArcFace)
       - Extract CLIP embedding
       - Store in Qdrant
    3. Return created character

    Args:
        db: Database session
        user_id: Owner user ID
        request: Character creation request

    Returns:
        Created Character entity
    """
    logger.info(f"[CHARACTER_CREATE] user={user_id} name={request.name}")

    # Create character entity
    character = Character(
        id=uuid.uuid4(),
        user_id=user_id,
        project_id=request.project_id,
        name=request.name,
        description=request.description,
        tags=request.tags or [],
        source_images=[],
        memory_keyframes=[],
        platform_refs={},
    )

    # Process initial reference image
    if request.reference_image or request.reference_image_url:
        image_data = await _get_image_data(
            base64_data=request.reference_image,
            image_url=request.reference_image_url,
        )
        if image_data:
            # Store source image
            image_url = await _upload_image(image_data, user_id, str(character.id))
            character.source_images = [{
                "url": image_url,
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": 1.0,
                "is_primary": True,
            }]
            character.primary_image_url = image_url

            # Extract and store embeddings
            qdrant_point_id = await _extract_and_store_embeddings(
                character_id=str(character.id),
                user_id=user_id,
                image_data=image_data,
                name=request.name,
                tags=request.tags or [],
            )
            character.qdrant_point_id = qdrant_point_id

    db.add(character)
    await db.commit()
    await db.refresh(character)

    logger.info(f"[CHARACTER_CREATE] created id={character.id}")
    return character


async def get_character(
    db: AsyncSession,
    character_id: uuid.UUID,
    user_id: str,
) -> Optional[Character]:
    """Get character by ID with ownership check."""
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_character(
    db: AsyncSession,
    character_id: uuid.UUID,
    user_id: str,
    request: CharacterUpdateRequest,
) -> Optional[Character]:
    """Update character metadata."""
    character = await get_character(db, character_id, user_id)
    if not character:
        return None

    if request.name is not None:
        character.name = request.name
    if request.description is not None:
        character.description = request.description
    if request.tags is not None:
        character.tags = request.tags
    if request.primary_image_url is not None:
        character.primary_image_url = request.primary_image_url

    await db.commit()
    await db.refresh(character)
    return character


async def delete_character(
    db: AsyncSession,
    character_id: uuid.UUID,
    user_id: str,
) -> bool:
    """Delete character and associated data."""
    character = await get_character(db, character_id, user_id)
    if not character:
        return False

    # Delete Qdrant point if exists
    if character.qdrant_point_id:
        await _delete_qdrant_point(character.qdrant_point_id)

    await db.delete(character)
    await db.commit()
    return True


async def list_characters(
    db: AsyncSession,
    user_id: str,
    project_id: Optional[uuid.UUID] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Character], int]:
    """List characters with optional filters."""
    query = select(Character).where(Character.user_id == user_id)

    if project_id:
        query = query.where(Character.project_id == project_id)
    if tags:
        # JSONB contains any of the tags
        query = query.where(Character.tags.contains(tags))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.order_by(Character.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)

    return list(result.scalars().all()), total


# ============================================================================
# Reference Image Management
# ============================================================================

async def add_reference_images(
    db: AsyncSession,
    character_id: uuid.UUID,
    user_id: str,
    image_urls: List[str] = None,
    images_base64: List[str] = None,
) -> Optional[Character]:
    """Add reference images to existing character.

    StoryMem Keyframe Selection Algorithm:
    1. Extract CLIP features for diversity analysis
    2. Score each image with HPSv3 aesthetic model
    3. Check face detection confidence
    4. Select diverse, high-quality images
    """
    character = await get_character(db, character_id, user_id)
    if not character:
        return None

    new_images = []

    # Process URL images
    for url in (image_urls or []):
        image_data = await _get_image_data(image_url=url)
        if image_data:
            uploaded_url = await _upload_image(image_data, user_id, str(character_id))
            quality_score = await _compute_quality_score(image_data)
            new_images.append({
                "url": uploaded_url,
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": quality_score,
                "is_primary": False,
            })

    # Process base64 images
    for b64 in (images_base64 or []):
        image_data = await _get_image_data(base64_data=b64)
        if image_data:
            uploaded_url = await _upload_image(image_data, user_id, str(character_id))
            quality_score = await _compute_quality_score(image_data)
            new_images.append({
                "url": uploaded_url,
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": quality_score,
                "is_primary": False,
            })

    if new_images:
        character.source_images = (character.source_images or []) + new_images

        # Update embeddings with new images
        if character.qdrant_point_id:
            await _update_embeddings(
                point_id=character.qdrant_point_id,
                source_images=[img["url"] for img in character.source_images],
            )

        await db.commit()
        await db.refresh(character)

    return character


# ============================================================================
# Memory Bank Management (StoryMem Algorithm)
# ============================================================================

async def update_memory_bank(
    db: AsyncSession,
    character_id: uuid.UUID,
    user_id: str,
    video_url: str,
    max_keyframes: int = 10,
    long_term_count: int = 5,
) -> Optional[MemoryBankResponse]:
    """Update memory bank from generated video.

    StoryMem Memory Bank Update Algorithm:
    1. Extract frames from video (1 FPS)
    2. Compute CLIP/Face embeddings for each frame
    3. Score with HPSv3 aesthetic model
    4. Apply keyframe selection criteria:
       - CLIP similarity to character reference
       - Aesthetic quality (HPSv3)
       - Face detection confidence
       - Diversity (minimum CLIP distance)
    5. Update long-term memory (best keyframes)
    6. Update sliding window (recent keyframes)
    """
    character = await get_character(db, character_id, user_id)
    if not character:
        return None

    logger.info(f"[MEMORY_BANK_UPDATE] character={character_id} video={video_url[:50]}...")

    config = KeyframeSelectionConfig()

    # Extract frames from video
    frames = await _extract_video_frames(video_url, fps=1)
    if not frames:
        logger.warning(f"[MEMORY_BANK_UPDATE] No frames extracted from video")
        return None

    # Get character reference embedding
    ref_embedding = await _get_character_embedding(character.qdrant_point_id)

    # Score each frame
    scored_frames = []
    for i, frame_data in enumerate(frames):
        timestamp = float(i)

        # Extract frame embedding
        frame_embedding = await _extract_clip_embedding(frame_data)

        # Compute scores
        clip_score = _compute_cosine_similarity(ref_embedding, frame_embedding) if ref_embedding else 0.7
        hps_score = await _compute_hps_score(frame_data)
        face_confidence = await _detect_face_confidence(frame_data)

        # Apply minimum thresholds
        if (clip_score >= config.min_clip_score and
            hps_score >= config.min_hps_score and
            face_confidence >= config.min_face_confidence):

            # Weighted score for ranking
            weighted_score = (
                clip_score * config.clip_weight +
                hps_score * config.hps_weight +
                face_confidence * config.face_weight
            )

            scored_frames.append({
                "frame_data": frame_data,
                "timestamp": timestamp,
                "clip_score": clip_score,
                "hps_score": hps_score,
                "face_confidence": face_confidence,
                "weighted_score": weighted_score,
                "embedding": frame_embedding,
            })

    # Sort by weighted score
    scored_frames.sort(key=lambda x: x["weighted_score"], reverse=True)

    # Select diverse keyframes
    selected_keyframes = _select_diverse_keyframes(
        scored_frames,
        max_count=max_keyframes,
        diversity_threshold=config.diversity_threshold,
    )

    # Upload selected keyframes
    new_keyframes = []
    for kf in selected_keyframes:
        frame_url = await _upload_image(kf["frame_data"], user_id, str(character_id))
        new_keyframes.append(MemoryKeyframe(
            frame_url=frame_url,
            timestamp=kf["timestamp"],
            clip_score=kf["clip_score"],
            hps_score=kf["hps_score"],
            face_confidence=kf["face_confidence"],
            is_long_term=False,
        ))

    # Update memory bank
    existing_keyframes = character.memory_keyframes or []
    existing_long_term = [kf for kf in existing_keyframes if kf.get("is_long_term")]
    existing_sliding = [kf for kf in existing_keyframes if not kf.get("is_long_term")]

    # Merge new keyframes into sliding window
    sliding_window = [kf.model_dump() for kf in new_keyframes] + existing_sliding
    sliding_window = sliding_window[:MAX_SLIDING_WINDOW_KEYFRAMES]

    # Update long-term memory (select best from all available)
    all_keyframes = existing_long_term + sliding_window
    all_keyframes.sort(key=lambda x: (
        x.get("clip_score", 0) * config.clip_weight +
        x.get("hps_score", 0) * config.hps_weight +
        x.get("face_confidence", 0) * config.face_weight
    ), reverse=True)

    # Mark top keyframes as long-term
    long_term = []
    for i, kf in enumerate(all_keyframes[:long_term_count]):
        kf["is_long_term"] = True
        long_term.append(kf)

    # Update remaining as sliding window
    updated_sliding = []
    for kf in all_keyframes[long_term_count:MAX_SLIDING_WINDOW_KEYFRAMES + long_term_count]:
        kf["is_long_term"] = False
        updated_sliding.append(kf)

    # Combine and save
    character.memory_keyframes = long_term + updated_sliding
    await db.commit()
    await db.refresh(character)

    # Build evidence refs (Vivid convention: List[str])
    evidence_refs = [
        f"db:characters:{character_id}",
    ]
    if character.qdrant_point_id:
        evidence_refs.append(f"qdrant:character_embeddings:{character.qdrant_point_id}")

    return MemoryBankResponse(
        character_id=character_id,
        keyframes_extracted=len(frames),
        long_term_updated=len(long_term),
        sliding_window_updated=len(updated_sliding),
        new_keyframes=new_keyframes,
        evidence_refs=evidence_refs,
    )


# ============================================================================
# Platform Synchronization
# ============================================================================

async def sync_to_platform(
    db: AsyncSession,
    character_id: uuid.UUID,
    user_id: str,
    platform: PlatformType,
    style_strength: float = 0.8,
) -> Optional[PlatformSyncResponse]:
    """Sync character to video generation platform.

    Platform-specific workflows:
    - Veo: Upload as Ingredient (max 3 per video)
    - Kling: Register as Element
    - Runway: Store as Reference
    """
    character = await get_character(db, character_id, user_id)
    if not character:
        return None

    if not character.primary_image_url:
        return PlatformSyncResponse(
            platform=platform,
            status="failed",
            message="Character has no primary image",
        )

    logger.info(f"[PLATFORM_SYNC] character={character_id} platform={platform.value}")

    try:
        if platform == PlatformType.VEO:
            ref_id = await _sync_to_veo(character)
        elif platform == PlatformType.KLING:
            ref_id = await _sync_to_kling(character)
        elif platform == PlatformType.RUNWAY:
            ref_id = await _sync_to_runway(character, style_strength)
        elif platform == PlatformType.HAILUO:
            ref_id = await _sync_to_hailuo(character)
        else:
            return PlatformSyncResponse(
                platform=platform,
                status="failed",
                message=f"Unsupported platform: {platform.value}",
            )

        # Update platform refs
        platform_refs = character.platform_refs or {}
        platform_refs[platform.value] = {
            "ref_id": ref_id,
            "last_sync": datetime.utcnow().isoformat(),
            "style_strength": style_strength if platform == PlatformType.RUNWAY else None,
        }
        character.platform_refs = platform_refs

        await db.commit()

        return PlatformSyncResponse(
            platform=platform,
            status="success",
            platform_ref_id=ref_id,
        )

    except Exception as e:
        logger.error(f"[PLATFORM_SYNC] Failed: {e}")
        return PlatformSyncResponse(
            platform=platform,
            status="failed",
            message=str(e),
        )


# ============================================================================
# Similarity Search
# ============================================================================

async def find_similar_characters(
    db: AsyncSession,
    character_id: uuid.UUID,
    user_id: str,
    limit: int = 5,
) -> List[CharacterSimilarity]:
    """Find similar characters using vector similarity.

    Uses Qdrant to search for characters with similar:
    - Face embeddings (identity)
    - CLIP embeddings (visual style)
    """
    character = await get_character(db, character_id, user_id)
    if not character or not character.qdrant_point_id:
        return []

    # Search Qdrant for similar embeddings
    similar_ids = await _search_similar_embeddings(
        point_id=character.qdrant_point_id,
        user_id=user_id,
        limit=limit + 1,  # +1 to exclude self
    )

    # Exclude self and fetch character details
    results = []
    for sim in similar_ids:
        if sim["character_id"] == str(character_id):
            continue

        char = await db.get(Character, uuid.UUID(sim["character_id"]))
        if char:
            results.append(CharacterSimilarity(
                character=CharacterSummaryResponse(
                    id=char.id,
                    name=char.name,
                    primary_image_url=char.primary_image_url,
                    tags=char.tags or [],
                    keyframe_count=char.keyframe_count,
                    platforms_synced=char.platforms_synced,
                ),
                similarity_score=sim["score"],
                match_type=sim.get("match_type", "combined"),
            ))

    return results[:limit]


# ============================================================================
# Helper Functions (Integrated with Real Services)
# ============================================================================

# Singleton services
_embedding_service: Optional[CharacterEmbeddingService] = None
_extractor = None


def _get_embedding_service() -> CharacterEmbeddingService:
    """Get singleton CharacterEmbeddingService."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = get_character_embedding_service()
    return _embedding_service


def _get_extractor():
    """Get singleton EmbeddingExtractor."""
    global _extractor
    if _extractor is None:
        _extractor = get_embedding_extractor()
    return _extractor


MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB max image size
MAX_BASE64_SIZE = MAX_IMAGE_SIZE * 4 // 3 + 100  # Base64 overhead + padding

# Blocked hosts for SSRF protection
_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}


def _validate_image_url(url: str) -> None:
    """Validate image URL for SSRF protection."""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme not allowed: {parsed.scheme}")

    hostname = parsed.hostname or ""
    if hostname in _BLOCKED_HOSTS:
        raise ValueError(f"URL host not allowed: {hostname}")

    # Block private IP ranges
    if hostname.startswith(("10.", "172.", "192.168.", "169.254.")):
        raise ValueError(f"Private IP addresses not allowed: {hostname}")


async def _get_image_data(
    base64_data: Optional[str] = None,
    image_url: Optional[str] = None,
) -> Optional[bytes]:
    """Fetch image data from base64 or URL with validation.

    Args:
        base64_data: Base64 encoded image data
        image_url: URL to fetch image from

    Returns:
        Image bytes or None on failure

    Note:
        - Max image size: 10MB
        - URLs are validated for SSRF protection
    """
    if base64_data:
        try:
            # Check base64 size limit before decoding
            if len(base64_data) > MAX_BASE64_SIZE:
                logger.warning(
                    f"Base64 data too large: {len(base64_data)} bytes (max {MAX_BASE64_SIZE})"
                )
                return None

            # Remove data URI prefix if present
            if "," in base64_data:
                base64_data = base64_data.split(",", 1)[1]

            decoded = base64.b64decode(base64_data)

            # Verify decoded size
            if len(decoded) > MAX_IMAGE_SIZE:
                logger.warning(
                    f"Decoded image too large: {len(decoded)} bytes (max {MAX_IMAGE_SIZE})"
                )
                return None

            return decoded
        except Exception as e:
            logger.warning(f"Failed to decode base64 image: {e}")
            return None

    if image_url:
        try:
            # Validate URL for SSRF protection
            _validate_image_url(image_url)

            async with httpx.AsyncClient(timeout=30) as client:
                # Stream download with size check
                async with client.stream("GET", image_url) as response:
                    response.raise_for_status()

                    # Check content-length header
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > MAX_IMAGE_SIZE:
                        logger.warning(
                            f"Image too large: {content_length} bytes (max {MAX_IMAGE_SIZE})"
                        )
                        return None

                    # Stream and accumulate with size limit
                    chunks = []
                    total_size = 0
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        total_size += len(chunk)
                        if total_size > MAX_IMAGE_SIZE:
                            logger.warning(
                                f"Image exceeds {MAX_IMAGE_SIZE} bytes during download"
                            )
                            return None
                        chunks.append(chunk)

                    return b"".join(chunks)
        except ValueError as e:
            logger.warning(f"URL validation failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch image URL: {e}")
            return None

    return None


async def _upload_image(
    image_data: bytes,
    user_id: str,
    character_id: str,
) -> str:
    """Upload image to storage and return URL.

    Uses StorageService for GCS (production) or local storage (development).
    """
    from app.services.storage_service import get_storage_service

    # Generate deterministic filename from content hash
    content_hash = hashlib.sha256(image_data).hexdigest()[:16]
    filename = f"characters/{user_id}/{character_id}/{content_hash}.jpg"

    # Upload using storage service (GCS or local depending on config)
    service = get_storage_service()
    return await service.upload_image(image_data, filename)


async def _extract_and_store_embeddings(
    character_id: str,
    user_id: str,
    image_data: bytes,
    name: str,
    tags: List[str],
) -> str:
    """Extract face, CLIP, style embeddings and store in Qdrant.

    2026 Pipeline:
    1. Extract ArcFace face embedding (512D)
    2. Extract CLIP visual embedding (768D)
    3. Extract style embedding + HPSv3 score (768D)
    4. Store as Named Vectors in Qdrant

    Args:
        character_id: Character UUID
        user_id: Owner user ID
        image_data: Raw image bytes
        name: Character name
        tags: Character tags

    Returns:
        Qdrant point ID
    """
    logger.info(f"[EMBEDDINGS] Extracting embeddings for character {character_id}")

    extractor = _get_extractor()
    service = _get_embedding_service()

    # Extract all embeddings in parallel
    embedding_result = await extractor.extract_all(image_data)

    if embedding_result.error:
        logger.warning(f"[EMBEDDINGS] Extraction error: {embedding_result.error}")

    # Store in Qdrant with named vectors
    point_id = await service.upsert_character(
        character_id=character_id,
        user_id=user_id,
        face_embed=embedding_result.face_embed,
        clip_embed=embedding_result.clip_embed,
        style_embed=embedding_result.style_embed,
        metadata={
            "name": name,
            "tags": tags,
            "hps_score": embedding_result.hps_score,
            "face_detected": embedding_result.face_detection.detected if embedding_result.face_detection else False,
            "face_confidence": embedding_result.face_detection.confidence if embedding_result.face_detection else 0.0,
        },
    )

    logger.info(f"[EMBEDDINGS] Stored embeddings for character {character_id} -> point {point_id}")
    return point_id


async def _update_embeddings(
    point_id: str,
    source_images: List[str],
) -> None:
    """Update Qdrant embeddings by averaging multiple source images.

    Args:
        point_id: Existing Qdrant point ID
        source_images: List of image URLs to process
    """
    logger.info(f"[EMBEDDINGS] Updating point {point_id} with {len(source_images)} images")

    if not source_images:
        return

    extractor = _get_extractor()
    service = _get_embedding_service()

    # Collect embeddings from all images
    all_face: List[List[float]] = []
    all_clip: List[List[float]] = []
    all_style: List[List[float]] = []

    for url in source_images[:MAX_REFERENCE_IMAGES]:  # Limit to 14 images (Gemini 3 Pro Image limit)
        try:
            image_data = await _get_image_data(image_url=url)
            if image_data:
                result = await extractor.extract_all(image_data)
                if result.face_embed:
                    all_face.append(result.face_embed)
                if result.clip_embed:
                    all_clip.append(result.clip_embed)
                if result.style_embed:
                    all_style.append(result.style_embed)
        except Exception as e:
            logger.warning(f"[EMBEDDINGS] Failed to process {url}: {e}")

    # Average embeddings
    def _average_embeddings(embeds: List[List[float]]) -> Optional[List[float]]:
        if not embeds:
            return None
        dim = len(embeds[0])
        avg = [sum(e[i] for e in embeds) / len(embeds) for i in range(dim)]
        # Normalize
        norm = sum(v ** 2 for v in avg) ** 0.5
        if norm > 0:
            avg = [v / norm for v in avg]
        return avg

    # Update Qdrant point
    await service.update_embeddings(
        point_id=point_id,
        face_embed=_average_embeddings(all_face),
        clip_embed=_average_embeddings(all_clip),
        style_embed=_average_embeddings(all_style),
    )


async def _delete_qdrant_point(point_id: str) -> None:
    """Delete point from Qdrant.

    Args:
        point_id: Qdrant point ID to delete
    """
    logger.info(f"[EMBEDDINGS] Deleting point {point_id}")

    service = _get_embedding_service()
    await service.delete_character(point_id)


async def _get_character_embedding(point_id: Optional[str]) -> Optional[List[float]]:
    """Get character reference CLIP embedding from Qdrant.

    Args:
        point_id: Qdrant point ID

    Returns:
        CLIP embedding (768D) or None
    """
    if not point_id:
        return None

    service = _get_embedding_service()
    char_embedding = await service.get_character_embedding(point_id)

    if char_embedding and char_embedding.clip_embed:
        return char_embedding.clip_embed

    return None


async def _extract_clip_embedding(image_data: bytes) -> List[float]:
    """Extract CLIP embedding from image.

    Args:
        image_data: Raw image bytes

    Returns:
        768D CLIP embedding
    """
    extractor = _get_extractor()
    clip_embed = await extractor.extract_clip_embedding(image_data)

    if clip_embed:
        return clip_embed

    # Fallback to zeros if extraction fails
    return [0.0] * CLIP_EMBED_DIM


async def _compute_hps_score(image_data: bytes) -> float:
    """Compute HPSv3 aesthetic score.

    Args:
        image_data: Raw image bytes

    Returns:
        HPS score (0.0-1.0)
    """
    extractor = _get_extractor()
    _, hps_score = await extractor.extract_style_embedding(image_data)

    return hps_score if hps_score is not None else 0.5


async def _detect_face_confidence(image_data: bytes) -> float:
    """Detect face and return confidence.

    Args:
        image_data: Raw image bytes

    Returns:
        Face detection confidence (0.0-1.0)
    """
    extractor = _get_extractor()
    _, face_detection = await extractor.extract_face_embedding(image_data)

    if face_detection and face_detection.detected:
        return face_detection.confidence

    return 0.0


async def _compute_quality_score(image_data: bytes) -> float:
    """Compute overall image quality score.

    Combines HPS aesthetic score with face detection confidence.

    Args:
        image_data: Raw image bytes

    Returns:
        Quality score (0.0-1.0)
    """
    extractor = _get_extractor()

    # Extract in parallel
    face_task = asyncio.create_task(extractor.extract_face_embedding(image_data))
    style_task = asyncio.create_task(extractor.extract_style_embedding(image_data))

    _, face_detection = await face_task
    _, hps_score = await style_task

    # Combine scores (weighted)
    face_conf = face_detection.confidence if face_detection and face_detection.detected else 0.5
    hps = hps_score if hps_score is not None else 0.5

    return 0.6 * hps + 0.4 * face_conf


def _compute_cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors using numpy for performance."""
    import numpy as np

    if not a or not b or len(a) != len(b):
        return 0.0

    arr_a, arr_b = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    norm_a, norm_b = np.linalg.norm(arr_a), np.linalg.norm(arr_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))


def _select_diverse_keyframes(
    scored_frames: List[Dict],
    max_count: int,
    diversity_threshold: float,
) -> List[Dict]:
    """Select diverse keyframes using greedy selection.

    StoryMem Diversity Algorithm:
    1. Start with highest-scored frame
    2. For each remaining frame:
       - Check CLIP distance to all selected frames
       - If minimum distance > threshold, add to selection
    3. Stop when max_count reached

    Args:
        scored_frames: List of frames with embeddings and scores
        max_count: Maximum keyframes to select
        diversity_threshold: Minimum CLIP distance for diversity

    Returns:
        Selected diverse keyframes
    """
    if not scored_frames:
        return []

    selected = [scored_frames[0]]

    for frame in scored_frames[1:]:
        if len(selected) >= max_count:
            break

        # Check diversity against all selected
        min_distance = min(
            1.0 - _compute_cosine_similarity(frame["embedding"], s["embedding"])
            for s in selected
        )

        if min_distance >= diversity_threshold:
            selected.append(frame)

    return selected


async def _extract_video_frames(video_url: str, fps: int = 1) -> List[bytes]:
    """Extract frames from video at specified FPS.

    TODO: Integrate with actual video processing (ffmpeg, moviepy)

    Args:
        video_url: URL of the video
        fps: Frames per second to extract

    Returns:
        List of frame image bytes
    """
    logger.info(f"[VIDEO_FRAMES] Extracting frames from {video_url[:50]}... at {fps} FPS")

    # TODO: Implement actual video frame extraction
    # try:
    #     import moviepy.editor as mp
    #     clip = mp.VideoFileClip(video_url)
    #     frames = []
    #     for t in range(0, int(clip.duration), 1 // fps):
    #         frame = clip.get_frame(t)
    #         # Convert numpy array to bytes
    #         ...
    #     return frames
    # except Exception as e:
    #     logger.error(f"Video frame extraction failed: {e}")

    return []


async def _search_similar_embeddings(
    point_id: str,
    user_id: str,
    limit: int,
) -> List[Dict[str, Any]]:
    """Search Qdrant for similar characters using CoFE fusion.

    Args:
        point_id: Source character's Qdrant point ID
        user_id: Filter by user ownership
        limit: Maximum results

    Returns:
        List of similar character dicts with scores
    """
    service = _get_embedding_service()

    # Get source character embedding
    source_embedding = await service.get_character_embedding(point_id)
    if not source_embedding:
        return []

    # Search similar using CoFE fusion
    results = await service.search_similar(
        query_embedding=source_embedding,
        user_id=user_id,
        limit=limit,
        vector_name="combined",  # CoFE multi-expert fusion
    )

    return [
        {
            "character_id": r.character_id,
            "score": r.score,
            "match_type": r.match_type,
            "metadata": r.metadata,
        }
        for r in results
    ]


# ============================================================================
# Platform Sync Implementations (Stubs)
# ============================================================================

async def _sync_to_veo(character: Character) -> str:
    """Sync character to Google Veo as Ingredient.

    TODO: Implement with Veo API when available
    """
    logger.info(f"[VEO_SYNC] Syncing character {character.id}")
    return f"veo_ingredient_{character.id}"


async def _sync_to_kling(character: Character) -> str:
    """Sync character to Kling as Element.

    TODO: Implement with Kling API
    """
    logger.info(f"[KLING_SYNC] Syncing character {character.id}")
    return f"kling_element_{character.id}"


async def _sync_to_runway(character: Character, style_strength: float) -> str:
    """Sync character to Runway as Reference.

    TODO: Implement with Runway API
    """
    logger.info(f"[RUNWAY_SYNC] Syncing character {character.id} strength={style_strength}")
    return f"runway_ref_{character.id}"


async def _sync_to_hailuo(character: Character) -> str:
    """Sync character to Hailuo.

    TODO: Implement with Hailuo API
    """
    logger.info(f"[HAILUO_SYNC] Syncing character {character.id}")
    return f"hailuo_ref_{character.id}"
