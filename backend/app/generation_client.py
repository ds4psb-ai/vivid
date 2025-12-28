"""Generation Client for AI Video Production.

This module implements Stage 10 of the E2E pipeline:
- Shot Contract → Prompt Contract conversion
- Gen Run execution (Veo 3.1 / Kling)
- Batch processing with iteration budget

Based on: 29_AI_PRODUCTION_PIPELINE_CODEX.md
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.storyboard_utils import build_shot_id, infer_shot_type, normalize_storyboard_cards

logger = logging.getLogger(__name__)


class GenProvider(str, Enum):
    """Available generation providers."""
    VEO = "veo"  # Google Veo 3.1
    KLING = "kling"  # Kling AI
    RUNWAY = "runway"  # Runway Gen-3
    MOCK = "mock"  # Mock for testing


class ConsistencyStrategy(str, Enum):
    """Consistency vs dynamics tradeoff."""
    TEXT_TO_VIDEO = "t2v"  # Better dynamics, less consistency
    IMAGE_TO_VIDEO = "i2v"  # Better consistency, less dynamics


@dataclass
class ShotContract:
    """Shot unit specification for generation."""
    shot_id: str
    sequence_id: str
    scene_id: str
    shot_type: str = "medium"  # wide, medium, close-up
    aspect_ratio: str = "16:9"
    lens: str = "50mm"
    film_stock: str = "Kodak Vision3"
    lighting: str = "natural"
    time_of_day: str = "day"
    mood: str = "neutral"
    character: Dict[str, Any] = field(default_factory=dict)
    pose_motion: str = ""
    dialogue: str = ""
    environment_layers: Dict[str, str] = field(default_factory=dict)
    continuity_tags: List[str] = field(default_factory=list)
    seed_image_ref: Optional[str] = None
    duration_sec: int = 4

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shot_id": self.shot_id,
            "sequence_id": self.sequence_id,
            "scene_id": self.scene_id,
            "shot_type": self.shot_type,
            "aspect_ratio": self.aspect_ratio,
            "lens": self.lens,
            "film_stock": self.film_stock,
            "lighting": self.lighting,
            "time_of_day": self.time_of_day,
            "mood": self.mood,
            "character": self.character,
            "pose_motion": self.pose_motion,
            "dialogue": self.dialogue,
            "environment_layers": self.environment_layers,
            "continuity_tags": self.continuity_tags,
            "seed_image_ref": self.seed_image_ref,
            "duration_sec": self.duration_sec,
        }


@dataclass
class PromptContract:
    """Generated prompt from Shot Contract."""
    shot_id: str
    prompt: str
    negative_prompt: str = ""
    strategy: ConsistencyStrategy = ConsistencyStrategy.TEXT_TO_VIDEO
    seed_image_url: Optional[str] = None
    duration_sec: int = 4
    aspect_ratio: str = "16:9"


@dataclass
class GenResult:
    """Result from generation run."""
    shot_id: str
    status: str  # success, failed, retrying
    output_url: Optional[str] = None
    iteration: int = 1
    error: Optional[str] = None
    latency_ms: int = 0
    cost_usd_est: float = 0.0
    model_version: str = ""


def shot_contract_to_prompt(contract: ShotContract) -> PromptContract:
    """Convert Shot Contract to Prompt Contract.
    
    Template structure from CODEX 29:
    [Shot Type], [Angle], [Aspect Ratio];
    Film stock / color treatment / grain;
    Lens + aperture;
    Character description + wardrobe;
    Pose/motion;
    Environment (foreground / midground / background);
    Lighting + mood;
    Dialogue (if any).
    """
    parts = []
    
    # Shot type, angle, aspect ratio
    parts.append(f"{contract.shot_type.title()} shot, {contract.aspect_ratio}")
    
    # Film stock / color treatment
    parts.append(f"{contract.film_stock}, light grain, cinematic contrast")
    
    # Lens
    parts.append(f"{contract.lens} lens")
    
    # Character
    if contract.character:
        char_name = contract.character.get("name", "character")
        char_desc = contract.character.get("notes", "")
        wardrobe = contract.character.get("wardrobe", "")
        if char_desc or wardrobe:
            parts.append(f"{char_name}, {char_desc}, {wardrobe}".strip(", "))
        else:
            parts.append(char_name)
    
    # Pose/motion
    if contract.pose_motion:
        parts.append(contract.pose_motion)
    
    # Environment layers
    env = contract.environment_layers
    if env:
        env_parts = []
        if env.get("foreground"):
            env_parts.append(f"Foreground: {env['foreground']}")
        if env.get("midground"):
            env_parts.append(f"Midground: {env['midground']}")
        if env.get("background"):
            env_parts.append(f"Background: {env['background']}")
        if env_parts:
            parts.append(". ".join(env_parts))
    
    # Lighting + mood
    parts.append(f"{contract.lighting}, {contract.mood}")
    
    prompt = ". ".join(parts) + "."
    
    # Determine strategy based on seed image
    strategy = (
        ConsistencyStrategy.IMAGE_TO_VIDEO 
        if contract.seed_image_ref 
        else ConsistencyStrategy.TEXT_TO_VIDEO
    )
    
    return PromptContract(
        shot_id=contract.shot_id,
        prompt=prompt,
        negative_prompt="cartoon, anime, low quality, blurry, distorted",
        strategy=strategy,
        seed_image_url=contract.seed_image_ref,
        duration_sec=contract.duration_sec,
        aspect_ratio=contract.aspect_ratio,
    )


async def _run_mock_generation(prompt: PromptContract) -> GenResult:
    """Mock generation for testing."""
    await asyncio.sleep(0.5)  # Simulate latency
    return GenResult(
        shot_id=prompt.shot_id,
        status="success",
        output_url=f"mock://generated/{prompt.shot_id}.mp4",
        iteration=1,
        latency_ms=500,
        cost_usd_est=0.0,
        model_version="mock-v1",
    )


async def _run_veo_generation(prompt: PromptContract) -> GenResult:
    """Run generation with Veo via Google Gen AI SDK.
    
    Veo generates 8-sec 720p/1080p videos with native audio.
    Uses the same API key as Gemini (GEMINI_API_KEY).
    
    Note: As of Dec 2024, Veo is primarily available through:
    - AI Studio web interface (aistudio.google.com)
    - Vertex AI (requires GCP project)
    
    This implementation attempts API access and provides helpful
    fallback information if not available.
    """
    import time
    start_time = time.time()
    
    if not settings.GEMINI_API_KEY:
        return GenResult(
            shot_id=prompt.shot_id,
            status="failed",
            error="GEMINI_API_KEY not configured",
            model_version="veo",
        )
    
    try:
        from google import genai
        from google.genai import types
        
        # Configure client
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Try available video models in order of preference
        models_to_try = [
            "veo-3.1-generate-preview",
            "veo-3.0-generate-001", 
            "veo-2.0-generate-001",
        ]
        
        logger.info(f"[Veo] Generating shot {prompt.shot_id}")
        logger.info(f"[Veo] Prompt: {prompt.prompt[:100]}...")
        
        for model_name in models_to_try:
            try:
                # Attempt video generation
                operation = client.models.generate_videos(
                    model=model_name,
                    prompt=prompt.prompt,
                    config=types.GenerateVideosConfig(
                        aspect_ratio=prompt.aspect_ratio,  # Use as-is (16:9 format)
                        duration_seconds=min(prompt.duration_sec, 8),
                        number_of_videos=1,
                    ),
                )
                
                # If we get here, model exists - poll for completion
                max_wait = 120
                poll_interval = 5
                elapsed = 0
                
                while not operation.done and elapsed < max_wait:
                    await asyncio.sleep(poll_interval)
                    operation = client.operations.get(operation)
                    elapsed += poll_interval
                    logger.debug(f"[Veo] Waiting... {elapsed}s")
                
                if operation.done and not operation.error:
                    result = operation.result
                    video_url = None
                    if hasattr(result, 'generated_videos') and result.generated_videos:
                        video = result.generated_videos[0]
                        video_url = video.uri if hasattr(video, 'uri') else str(video)
                    
                    if video_url:
                        return GenResult(
                            shot_id=prompt.shot_id,
                            status="success",
                            output_url=video_url,
                            iteration=1,
                            latency_ms=int((time.time() - start_time) * 1000),
                            cost_usd_est=0.05,
                            model_version=model_name,
                        )
                        
            except Exception as model_error:
                if "NOT_FOUND" in str(model_error):
                    continue  # Try next model
                raise
        
        # No models worked - provide informative message
        return GenResult(
            shot_id=prompt.shot_id,
            status="failed",
            error="Veo not yet available via API. Use AI Studio web or Vertex AI.",
            latency_ms=int((time.time() - start_time) * 1000),
            model_version="veo-unavailable",
        )
        
    except Exception as e:
        logger.error(f"[Veo] Generation failed: {e}")
        return GenResult(
            shot_id=prompt.shot_id,
            status="failed",
            error=str(e),
            latency_ms=int((time.time() - start_time) * 1000),
            model_version="veo",
        )


async def _run_kling_generation(prompt: PromptContract) -> GenResult:
    """Run generation with Kling AI.
    
    Kling is an alternative provider, typically accessed via their own API.
    For now, falls back to mock - can be implemented when API access is available.
    """
    logger.info(f"[Kling] Would generate shot {prompt.shot_id}")
    logger.info(f"[Kling] Note: Kling API integration pending - using mock")
    
    # Fallback to mock for now
    await asyncio.sleep(0.5)
    return GenResult(
        shot_id=prompt.shot_id,
        status="success",
        output_url=f"kling-mock://generated/{prompt.shot_id}.mp4",
        iteration=1,
        latency_ms=500,
        cost_usd_est=0.03,
        model_version="kling-mock",
    )


async def generate_shot(
    contract: ShotContract,
    provider: GenProvider = GenProvider.MOCK,
    max_iterations: int = 4,
) -> GenResult:
    """Generate a single shot from Shot Contract.
    
    Args:
        contract: Shot specification.
        provider: Generation provider to use.
        max_iterations: Max retry attempts (budget 3-4 per CODEX 29).
        
    Returns:
        GenResult with output or error.
    """
    # Convert to prompt
    prompt_contract = shot_contract_to_prompt(contract)
    logger.info(f"Generated prompt for {contract.shot_id}: {prompt_contract.prompt[:80]}...")
    
    for iteration in range(1, max_iterations + 1):
        try:
            if provider == GenProvider.MOCK:
                result = await _run_mock_generation(prompt_contract)
            elif provider == GenProvider.VEO:
                result = await _run_veo_generation(prompt_contract)
            elif provider == GenProvider.KLING:
                result = await _run_kling_generation(prompt_contract)
            else:
                result = await _run_mock_generation(prompt_contract)
            
            result.iteration = iteration
            
            if result.status == "success":
                return result
                
        except Exception as e:
            logger.warning(f"Generation attempt {iteration} failed: {e}")
            if iteration == max_iterations:
                return GenResult(
                    shot_id=contract.shot_id,
                    status="failed",
                    iteration=iteration,
                    error=str(e),
                )
    
    return GenResult(
        shot_id=contract.shot_id,
        status="failed",
        iteration=max_iterations,
        error="Max iterations exceeded",
    )


async def generate_batch(
    contracts: List[ShotContract],
    provider: GenProvider = GenProvider.MOCK,
    batch_size: int = 5,
    max_iterations: int = 4,
) -> List[GenResult]:
    """Generate shots in batches (5-10 per CODEX 29).
    
    Args:
        contracts: List of shot specifications.
        provider: Generation provider.
        batch_size: Concurrent batch size (5-10 recommended).
        max_iterations: Max retry per shot.
        
    Returns:
        List of GenResults.
    """
    results = []
    
    for i in range(0, len(contracts), batch_size):
        batch = contracts[i:i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} shots)")
        
        batch_results = await asyncio.gather(*[
            generate_shot(contract, provider, max_iterations)
            for contract in batch
        ])
        results.extend(batch_results)
    
    return results


def create_shot_contracts_from_storyboard(
    storyboard_cards: List[Dict[str, Any]],
    sequence_id: str = "seq-01",
    scene_id: str = "scene-01",
) -> List[ShotContract]:
    """Convert storyboard cards to shot contracts.
    
    This bridges Stage 8 (Storyboard) to Stage 10 (Generate).
    """
    contracts = []
    
    normalized_cards = normalize_storyboard_cards(storyboard_cards, sequence_id=sequence_id)
    for i, card in enumerate(normalized_cards):
        raw_id = (
            card.get("shot_id")
            or card.get("card_id")
            or card.get("id")
            or card.get("shot")
            or (i + 1)
        )
        shot_id = card.get("shot_id") or build_shot_id(raw_id, i + 1, sequence_id=sequence_id)
        raw_shot = card.get("shot_type") or card.get("shot")
        shot_type = infer_shot_type(raw_shot)
        description = (
            card.get("description")
            or card.get("note")
            or card.get("summary")
            or ""
        )
        
        contract = ShotContract(
            shot_id=shot_id,
            sequence_id=sequence_id,
            scene_id=scene_id,
            shot_type=shot_type,
            aspect_ratio=card.get("aspect_ratio", "16:9"),
            lens=card.get("lens", "50mm"),
            lighting=card.get("lighting", "natural"),
            mood=card.get("mood", "neutral"),
            pose_motion=description,
            dialogue=card.get("dialogue"),
            seed_image_ref=card.get("seed_image_ref") or f"nb:storyboard:{shot_id}",
            duration_sec=card.get("duration_sec", 4),
        )
        contracts.append(contract)
    
    return contracts


# ─────────────────────────────────────────────────────────────────────────────
# E2E Pipeline Integration
# ─────────────────────────────────────────────────────────────────────────────

async def run_generation_pipeline(
    storyboard_cards: List[Dict[str, Any]],
    provider: GenProvider = GenProvider.MOCK,
    sequence_id: str = "seq-01",
    scene_id: str = "scene-01",
) -> Tuple[List[GenResult], Dict[str, Any]]:
    """Run full generation pipeline from storyboard cards.
    
    Pipeline:
    1. Storyboard Cards → Shot Contracts
    2. Shot Contracts → Prompt Contracts
    3. Prompt Contracts → Gen Runs (batch)
    4. Collect results + metrics
    
    Returns:
        Tuple of (results, metrics).
    """
    start_time = datetime.utcnow()
    
    # Step 1: Create shot contracts
    contracts = create_shot_contracts_from_storyboard(
        storyboard_cards, sequence_id, scene_id
    )
    logger.info(f"Created {len(contracts)} shot contracts")
    
    # Step 2-3: Generate in batches
    results = await generate_batch(contracts, provider)
    
    # Step 4: Collect metrics
    success_count = sum(1 for r in results if r.status == "success")
    total_latency = sum(r.latency_ms for r in results)
    total_cost = sum(r.cost_usd_est for r in results)
    
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    
    metrics = {
        "total_shots": len(contracts),
        "success_count": success_count,
        "failure_count": len(contracts) - success_count,
        "success_rate": success_count / len(contracts) if contracts else 0,
        "total_latency_ms": total_latency,
        "total_cost_usd": total_cost,
        "pipeline_duration_sec": elapsed,
        "provider": provider.value,
    }
    
    return results, metrics
