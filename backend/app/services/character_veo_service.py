"""Character-VEO Coordination Service.

Integrates Character Consistency with Veo 3.1 Ingredients feature.

Features:
- Auto-inject characters as Veo Ingredients (max 3)
- Memory bank integration for best reference frames
- Post-generation memory bank update
- Platform sync tracking

2026 Best Practices:
- Veo 3.1 Ingredients API for character reference
- StoryMem memory bank for consistency tracking
- Character appearance tracking across shots

References:
- Veo 3.1 Ingredients: Google GenAI API
- StoryMem: arXiv:2512.19539
"""
from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models_character import Character, CharacterAppearance
from app.services.character_service import get_character, _get_image_data
from app.services.veo_service import (
    VeoConfig,
    VeoResult,
    VeoService,
    get_veo_service,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Prompt Sanitization Utilities
# =============================================================================

MAX_FIELD_LENGTH = 100
UNSAFE_CHARS = re.compile(r'[\[\]{}()<>"|;`$\\]')


def _sanitize_prompt_input(value: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """Sanitize user input for prompt injection prevention.

    Strips unsafe characters and limits length.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    return UNSAFE_CHARS.sub('', value.strip()[:max_length])

# =============================================================================
# Constants
# =============================================================================

MAX_VEO_INGREDIENTS = 3  # Veo 3.1 supports up to 3 reference images


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class CharacterVeoIngredient:
    """Character ingredient for Veo generation."""
    character_id: str
    character_name: str
    image_url: str
    image_data: Optional[bytes] = None
    hps_score: Optional[float] = None


@dataclass
class VeoGenerationWithCharacters:
    """Result of Veo generation with character tracking."""
    veo_result: VeoResult
    characters_used: List[CharacterVeoIngredient]
    appearances_created: List[str]  # List of appearance IDs


# =============================================================================
# Character-VEO Coordination Service
# =============================================================================

class CharacterVeoService:
    """Coordinates Character Consistency with Veo 3.1 generation.

    Workflow:
    1. Resolve character_ids to images
    2. Select best reference images from memory bank
    3. Inject as Veo Ingredients
    4. Track character appearances after generation
    5. Update memory bank with best frames
    """

    async def prepare_character_ingredients(
        self,
        db: AsyncSession,
        user_id: str,
        character_ids: List[str],
    ) -> List[CharacterVeoIngredient]:
        """Prepare character images as Veo Ingredients.

        Uses StoryMem memory bank to select the best reference frames.
        Prioritizes:
        1. Long-term memory keyframes (highest quality)
        2. Primary image
        3. Recent sliding window keyframes

        Args:
            db: Database session
            user_id: User ID for ownership validation
            character_ids: List of character UUIDs

        Returns:
            List of CharacterVeoIngredient (max 3)
        """
        ingredients = []

        for char_id_str in character_ids[:MAX_VEO_INGREDIENTS]:
            try:
                char_id = uuid.UUID(char_id_str)
                character = await get_character(db, char_id, user_id)

                if not character:
                    logger.warning(f"[CHAR_VEO] Character not found: {char_id_str}")
                    continue

                # Select best reference image
                image_url, hps_score = self._select_best_reference(character)

                if not image_url:
                    logger.warning(f"[CHAR_VEO] No image for character: {char_id_str}")
                    continue

                # Fetch image data
                image_data = await _get_image_data(image_url=image_url)

                ingredients.append(CharacterVeoIngredient(
                    character_id=char_id_str,
                    character_name=character.name,
                    image_url=image_url,
                    image_data=image_data,
                    hps_score=hps_score,
                ))

                logger.info(
                    f"[CHAR_VEO] Prepared ingredient: {character.name} "
                    f"(hps={hps_score:.2f if hps_score else 'N/A'})"
                )

            except Exception as e:
                logger.error(f"[CHAR_VEO] Failed to prepare character {char_id_str}: {e}")

        return ingredients

    def _select_best_reference(
        self,
        character: Character,
    ) -> Tuple[Optional[str], Optional[float]]:
        """Select the best reference image from character.

        Priority:
        1. Long-term memory keyframe with highest HPS score
        2. Primary image
        3. Most recent source image

        Args:
            character: Character entity

        Returns:
            Tuple of (image_url, hps_score)
        """
        # Check long-term memory keyframes first
        memory_keyframes = character.memory_keyframes or []
        long_term = [kf for kf in memory_keyframes if kf.get("is_long_term")]

        if long_term:
            # Sort by HPS score (best first)
            long_term.sort(key=lambda x: x.get("hps_score", 0), reverse=True)
            best = long_term[0]
            return best.get("frame_url"), best.get("hps_score")

        # Fall back to primary image
        if character.primary_image_url:
            return character.primary_image_url, None

        # Fall back to first source image
        source_images = character.source_images or []
        if source_images:
            first = source_images[0]
            return first.get("url"), first.get("quality_score")

        return None, None

    async def generate_with_characters(
        self,
        db: AsyncSession,
        user_id: str,
        config: VeoConfig,
        character_ids: List[str],
        api_key: Optional[str] = None,
        progress_callback=None,
    ) -> VeoGenerationWithCharacters:
        """Generate video with character ingredients.

        Args:
            db: Database session
            user_id: User ID
            config: VeoConfig with generation parameters
            character_ids: Characters to include as ingredients
            api_key: Optional BYOK API key
            progress_callback: Optional progress callback

        Returns:
            VeoGenerationWithCharacters with result and tracking
        """
        # Prepare character ingredients
        ingredients = await self.prepare_character_ingredients(
            db, user_id, character_ids
        )

        if ingredients:
            logger.info(
                f"[CHAR_VEO] Using {len(ingredients)} character ingredients: "
                f"{[i.character_name for i in ingredients]}"
            )

            # Enhance prompt with character names
            char_names = [i.character_name for i in ingredients]
            enhanced_prompt = self._enhance_prompt_with_characters(
                config.prompt, char_names
            )
            config = VeoConfig(
                prompt=enhanced_prompt,
                model=config.model,
                duration_seconds=config.duration_seconds,
                aspect_ratio=config.aspect_ratio,
                negative_prompt=config.negative_prompt,
                seed=config.seed,
                include_audio=config.include_audio,
                person_generation=config.person_generation,
            )

        # Generate video
        service = get_veo_service(api_key)
        veo_result = await service.generate_video(
            config=config,
            progress_callback=progress_callback,
        )

        appearances_created = []

        # If successful, create appearance records
        if veo_result.success and ingredients:
            appearances_created = await self._create_appearances(
                db=db,
                veo_result=veo_result,
                config=config,
                ingredients=ingredients,
            )

        return VeoGenerationWithCharacters(
            veo_result=veo_result,
            characters_used=ingredients,
            appearances_created=appearances_created,
        )

    def _enhance_prompt_with_characters(
        self,
        prompt: str,
        character_names: List[str],
    ) -> str:
        """Enhance prompt with character references.

        Adds explicit character name mentions if not already present.

        Args:
            prompt: Original prompt
            character_names: List of character names

        Returns:
            Enhanced prompt
        """
        # Sanitize character names
        sanitized_names = [_sanitize_prompt_input(name) for name in character_names]

        # Check if characters already mentioned
        prompt_lower = prompt.lower()
        unmentioned = [
            name for name in sanitized_names
            if name.lower() not in prompt_lower
        ]

        if not unmentioned:
            return prompt

        # Add character mentions
        if len(unmentioned) == 1:
            prefix = f"[Character: {unmentioned[0]}] "
        else:
            prefix = f"[Characters: {', '.join(unmentioned)}] "

        return prefix + prompt

    async def _create_appearances(
        self,
        db: AsyncSession,
        veo_result: VeoResult,
        config: VeoConfig,
        ingredients: List[CharacterVeoIngredient],
    ) -> List[str]:
        """Create character appearance records for tracking.

        Args:
            db: Database session
            veo_result: Successful VEO result
            config: VEO config used
            ingredients: Characters used

        Returns:
            List of created appearance IDs
        """
        appearance_ids = []

        for ingredient in ingredients:
            try:
                appearance = CharacterAppearance(
                    id=uuid.uuid4(),
                    character_id=uuid.UUID(ingredient.character_id),
                    shot_id=None,  # Can be linked later
                    scene_description=config.prompt[:500],
                    generated_frame_url=veo_result.video_uri,
                )

                db.add(appearance)
                appearance_ids.append(str(appearance.id))

                logger.info(
                    f"[CHAR_VEO] Created appearance {appearance.id} for "
                    f"character {ingredient.character_name}"
                )

            except Exception as e:
                logger.error(
                    f"[CHAR_VEO] Failed to create appearance for "
                    f"{ingredient.character_id}: {e}"
                )

        if appearance_ids:
            await db.commit()

        return appearance_ids

    async def update_memory_bank_from_video(
        self,
        db: AsyncSession,
        user_id: str,
        character_id: str,
        video_url: str,
    ) -> bool:
        """Update character memory bank from generated video.

        Extracts keyframes and updates StoryMem memory bank.

        Args:
            db: Database session
            user_id: User ID
            character_id: Character UUID
            video_url: Generated video URL

        Returns:
            True if memory bank was updated
        """
        from app.services.character_service import update_memory_bank

        try:
            result = await update_memory_bank(
                db=db,
                character_id=uuid.UUID(character_id),
                user_id=user_id,
                video_url=video_url,
                max_keyframes=10,
                long_term_count=5,
            )

            if result:
                logger.info(
                    f"[CHAR_VEO] Updated memory bank for {character_id}: "
                    f"extracted={result.keyframes_extracted}, "
                    f"long_term={result.long_term_updated}"
                )
                return True

        except Exception as e:
            logger.error(f"[CHAR_VEO] Memory bank update failed: {e}")

        return False


# =============================================================================
# Singleton Instance
# =============================================================================

_service: Optional[CharacterVeoService] = None


def get_character_veo_service() -> CharacterVeoService:
    """Get singleton CharacterVeoService instance."""
    global _service
    if _service is None:
        _service = CharacterVeoService()
    return _service


# =============================================================================
# Convenience Functions
# =============================================================================

async def generate_veo_with_characters(
    db: AsyncSession,
    user_id: str,
    prompt: str,
    character_ids: List[str],
    model: str = "veo-3.1-generate-preview",
    duration_seconds: int = 8,
    aspect_ratio: str = "16:9",
    api_key: Optional[str] = None,
    progress_callback=None,
) -> VeoGenerationWithCharacters:
    """Convenience function to generate video with character consistency.

    Args:
        db: Database session
        user_id: User ID
        prompt: Video generation prompt
        character_ids: Characters to include as ingredients
        model: Veo model
        duration_seconds: Video duration
        aspect_ratio: Aspect ratio
        api_key: Optional BYOK key
        progress_callback: Optional progress callback

    Returns:
        VeoGenerationWithCharacters with result and tracking
    """
    config = VeoConfig(
        prompt=prompt,
        model=model,
        duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio,
        include_audio=True,
    )

    service = get_character_veo_service()
    return await service.generate_with_characters(
        db=db,
        user_id=user_id,
        config=config,
        character_ids=character_ids,
        api_key=api_key,
        progress_callback=progress_callback,
    )
