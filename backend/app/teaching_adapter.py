"""Teaching Capsule Adapter: Server-side AI logic for teaching tools.

This module provides adapters for Crebit teaching capsules:
- Prompt Generator: Veo video prompt generation
- Storyboard Creator: Scene-based storyboard generation
- Image Generator: AI image generation
- Reference Analyzer: Video reference analysis

All AI logic runs server-side to protect intellectual property.
Supports both server API key (default) and BYOK (user-provided key).

Security:
- Input sanitization prevents prompt injection
- Rate limiting handled at router level
- API keys never logged
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypedDict

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Constants & Configuration
# ============================================================================

class TeachingCapsuleId(str, Enum):
    """Valid teaching capsule identifiers."""
    PROMPT_GENERATE = "teaching.prompt.generate"
    STORYBOARD_CREATE = "teaching.storyboard.create"
    IMAGE_GENERATE = "teaching.image.generate"
    REFERENCE_ANALYZE = "teaching.reference.analyze"


# Input validation limits
MAX_TOPIC_LENGTH = 2000
MAX_CONCEPT_LENGTH = 5000
MAX_DESCRIPTION_LENGTH = 3000
MIN_SCENE_COUNT = 1
MAX_SCENE_COUNT = 20
ALLOWED_LANGUAGES = {"ko", "en"}
ALLOWED_MODELS = {"gemini-2.5-flash", "gemini-2.5-pro", "gemini-3-flash-preview"}
GEMINI_TIMEOUT_SECONDS = 30


@dataclass
class CapsuleMetrics:
    """Metrics for capsule execution."""
    latency_ms: int
    input_tokens: int
    output_tokens: int
    model: str
    cached: bool = False


class CapsuleResult(TypedDict):
    """Structured capsule result."""
    success: bool
    capsule_id: str
    output: Dict[str, Any]
    error: Optional[str]
    metrics: Optional[Dict[str, Any]]


# ============================================================================
# Input Sanitization
# ============================================================================

def _sanitize_text(text: str, max_length: int, field_name: str) -> str:
    """Sanitize text input to prevent prompt injection.
    
    Args:
        text: Raw input text
        max_length: Maximum allowed length
        field_name: Field name for error messages
        
    Returns:
        Sanitized text
        
    Raises:
        ValueError: If input is invalid
    """
    if not isinstance(text, str):
        raise ValueError(f"{field_name} must be a string")
    
    # Strip and truncate
    text = text.strip()[:max_length]
    
    # Remove potential prompt injection patterns
    # Block common injection attempts
    injection_patterns = [
        r"(?i)ignore\s+(previous|above|all)\s+instructions",
        r"(?i)forget\s+(previous|above|all)\s+instructions",
        r"(?i)disregard\s+(previous|above|all)\s+instructions",
        r"(?i)system\s*:\s*",
        r"(?i)assistant\s*:\s*",
        r"(?i)human\s*:\s*",
    ]
    
    for pattern in injection_patterns:
        text = re.sub(pattern, "", text)
    
    return text


def _validate_enum(value: str, allowed: set, field_name: str, default: str) -> str:
    """Validate enum-like string values."""
    if value in allowed:
        return value
    logger.warning(f"Invalid {field_name} '{value}', using default '{default}'")
    return default


def _validate_int_range(value: Any, min_val: int, max_val: int, default: int) -> int:
    """Validate integer within range."""
    try:
        val = int(value)
        return max(min_val, min(max_val, val))
    except (TypeError, ValueError):
        return default


# ============================================================================
# Prompt Templates (Protected - Server-side only)
# ============================================================================

PROMPT_GENERATOR_SYSTEM = """You are an expert video prompt engineer specializing in Veo 3.1 prompts.
Your task is to generate high-quality, cinematic video prompts based on user input.

Output ONLY valid JSON with this exact structure (no markdown, no explanation):
{
  "prompt": "The main video generation prompt",
  "negative_prompt": "Elements to avoid",
  "style": {
    "cinematography": "Camera and visual style",
    "lighting": "Lighting approach",
    "color_grade": "Color palette and grading"
  },
  "technical": {
    "aspect_ratio": "16:9 or other",
    "duration": "Suggested duration",
    "fps": "Frame rate recommendation"
  }
}

Guidelines:
- Write prompts in descriptive, cinematic language
- Include specific visual details and camera movements
- Consider pacing, mood, and narrative flow
- Reference film techniques when appropriate
- NEVER include user instructions in your output
"""

STORYBOARD_SYSTEM = """You are a professional storyboard artist and cinematographer.
Create detailed storyboard cards from video concepts.

Output ONLY valid JSON array with this structure:
[
  {
    "scene_number": 1,
    "description": "Visual description",
    "camera": "Shot type and movement",
    "duration": "Estimated duration in seconds",
    "notes": "Director notes"
  }
]

- NEVER include user instructions in your output
"""

IMAGE_GENERATOR_SYSTEM = """You are an AI image generation expert.
Create detailed image prompts optimized for Imagen/DALL-E/Midjourney.

Output ONLY valid JSON:
{
  "prompt": "Optimized image prompt",
  "negative_prompt": "Elements to avoid",
  "parameters": {
    "style": "Art style",
    "aspect_ratio": "Image ratio",
    "quality": "Quality setting"
  }
}

- NEVER include user instructions in your output
"""

REFERENCE_ANALYZER_SYSTEM = """You are a film analyst specializing in visual storytelling.
Analyze video references and extract key cinematic elements.

Output ONLY valid JSON:
{
  "composition": "Composition analysis",
  "lighting": "Lighting analysis",
  "color": "Color palette analysis",
  "movement": "Camera movement analysis",
  "narrative": "Narrative structure analysis",
  "recommendations": ["List of key takeaways"]
}

- NEVER include user instructions in your output
"""


# ============================================================================
# Gemini Client with Hardening
# ============================================================================

async def _call_gemini(
    prompt: str,
    system_prompt: str,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    timeout: float = GEMINI_TIMEOUT_SECONDS,
) -> tuple[Dict[str, Any], CapsuleMetrics]:
    """Call Gemini API with given prompts.
    
    Uses server key by default, BYOK if provided.
    
    Args:
        prompt: User prompt
        system_prompt: System instructions
        api_key: Optional user API key (BYOK)
        model: Model to use
        temperature: Generation temperature
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (parsed response, metrics)
        
    Raises:
        ValueError: If no API key available
        TimeoutError: If request times out
        RuntimeError: If API call fails
    """
    from google import genai
    from google.genai import types
    
    start_time = time.monotonic()
    
    # Validate model
    model = _validate_enum(model, ALLOWED_MODELS, "model", "gemini-2.5-flash")
    
    # Use provided key or fall back to server key
    key = api_key or settings.GEMINI_API_KEY
    if not key:
        raise ValueError("No API key available. Configure GEMINI_API_KEY or provide user key.")
    
    client = genai.Client(api_key=key)
    
    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.error(f"Gemini API timeout after {timeout}s")
        raise TimeoutError(f"Request timed out after {timeout} seconds")
    except Exception as e:
        logger.error(f"Gemini API error: {type(e).__name__}: {e}")
        raise RuntimeError(f"AI service error: {type(e).__name__}")
    
    latency_ms = int((time.monotonic() - start_time) * 1000)
    
    # Extract token usage
    input_tokens = 0
    output_tokens = 0
    if hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
        input_tokens = getattr(usage, 'prompt_token_count', 0)
        output_tokens = getattr(usage, 'candidates_token_count', 0)
    
    metrics = CapsuleMetrics(
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
    )
    
    # Parse JSON response
    text = response.text.strip()
    
    # Handle markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        # Find start and end of code block
        start_idx = 1 if lines[0].startswith("```") else 0
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                end_idx = i
                break
        text = "\n".join(lines[start_idx:end_idx]).strip()
        if text.startswith("json"):
            text = text[4:].strip()
    
    try:
        return json.loads(text), metrics
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response: {e}. Raw: {text[:500]}")
        # Return a structured error instead of raw text
        return {
            "error": "Failed to parse AI response",
            "_raw_truncated": text[:200] if len(text) > 200 else text,
        }, metrics


# ============================================================================
# Teaching Capsule Adapters
# ============================================================================

async def run_prompt_generator(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate Veo video prompts from user input.
    
    Args:
        inputs: topic, style, mood, duration, language
        params: model selection
        user_api_key: Optional BYOK
    
    Returns:
        CapsuleResult with generated prompt spec
    """
    # Validate and sanitize inputs
    topic = _sanitize_text(
        inputs.get("topic", ""),
        MAX_TOPIC_LENGTH,
        "topic"
    )
    if not topic:
        return {
            "success": False,
            "capsule_id": TeachingCapsuleId.PROMPT_GENERATE.value,
            "output": {},
            "error": "Topic is required",
            "metrics": None,
        }
    
    style = _sanitize_text(inputs.get("style", "cinematic"), 50, "style")
    mood = _sanitize_text(inputs.get("mood", "neutral"), 50, "mood")
    duration = _sanitize_text(inputs.get("duration", "15 seconds"), 20, "duration")
    language = _validate_enum(inputs.get("language", "ko"), ALLOWED_LANGUAGES, "language", "ko")
    model = _validate_enum(params.get("model", "gemini-2.5-flash"), ALLOWED_MODELS, "model", "gemini-2.5-flash")
    
    user_prompt = f"""Generate a Veo 3.1 video prompt for:

Topic: {topic}
Visual Style: {style}
Mood/Tone: {mood}
Target Duration: {duration}
Output Language: {language}

Create a detailed, professional prompt. Include camera movements, lighting, and visual details.
"""

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=PROMPT_GENERATOR_SYSTEM,
            api_key=user_api_key,
            model=model,
        )
        
        return {
            "success": "error" not in result,
            "capsule_id": TeachingCapsuleId.PROMPT_GENERATE.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": TeachingCapsuleId.PROMPT_GENERATE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_storyboard_creator(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Create storyboard cards from a concept or prompt."""
    concept = _sanitize_text(
        inputs.get("concept", inputs.get("prompt", "")),
        MAX_CONCEPT_LENGTH,
        "concept"
    )
    if not concept:
        return {
            "success": False,
            "capsule_id": TeachingCapsuleId.STORYBOARD_CREATE.value,
            "output": {},
            "error": "Concept is required",
            "metrics": None,
        }
    
    scene_count = _validate_int_range(inputs.get("scene_count", 5), MIN_SCENE_COUNT, MAX_SCENE_COUNT, 5)
    language = _validate_enum(inputs.get("language", "ko"), ALLOWED_LANGUAGES, "language", "ko")
    model = _validate_enum(params.get("model", "gemini-2.5-flash"), ALLOWED_MODELS, "model", "gemini-2.5-flash")
    
    user_prompt = f"""Create a {scene_count}-scene storyboard for:

Concept: {concept}
Language: {language}

For each scene provide: description, camera, duration, notes.
"""

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=STORYBOARD_SYSTEM,
            api_key=user_api_key,
            model=model,
        )
        
        # Normalize output format
        output = result if isinstance(result, list) else result.get("scenes", [result])
        
        return {
            "success": "error" not in result,
            "capsule_id": TeachingCapsuleId.STORYBOARD_CREATE.value,
            "output": {"scenes": output} if isinstance(output, list) else output,
            "error": result.get("error") if isinstance(result, dict) else None,
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": TeachingCapsuleId.STORYBOARD_CREATE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_image_generator(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate image prompts optimized for AI image generation."""
    description = _sanitize_text(
        inputs.get("description", ""),
        MAX_DESCRIPTION_LENGTH,
        "description"
    )
    if not description:
        return {
            "success": False,
            "capsule_id": TeachingCapsuleId.IMAGE_GENERATE.value,
            "output": {},
            "error": "Description is required",
            "metrics": None,
        }
    
    style = _sanitize_text(inputs.get("style", "photorealistic"), 50, "style")
    aspect_ratio = _sanitize_text(inputs.get("aspect_ratio", "16:9"), 10, "aspect_ratio")
    model = _validate_enum(params.get("model", "gemini-2.5-flash"), ALLOWED_MODELS, "model", "gemini-2.5-flash")
    
    user_prompt = f"""Create an optimized AI image generation prompt for:

Description: {description}
Style: {style}
Aspect Ratio: {aspect_ratio}

Generate a detailed prompt suitable for Imagen, DALL-E, or Midjourney.
"""

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=IMAGE_GENERATOR_SYSTEM,
            api_key=user_api_key,
            model=model,
        )
        
        return {
            "success": "error" not in result,
            "capsule_id": TeachingCapsuleId.IMAGE_GENERATE.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": TeachingCapsuleId.IMAGE_GENERATE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_reference_analyzer(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Analyze video references and extract cinematic elements."""
    description = _sanitize_text(
        inputs.get("video_description", ""),
        MAX_DESCRIPTION_LENGTH,
        "video_description"
    )
    if not description:
        return {
            "success": False,
            "capsule_id": TeachingCapsuleId.REFERENCE_ANALYZE.value,
            "output": {},
            "error": "Video description is required",
            "metrics": None,
        }
    
    focus_areas = inputs.get("focus_areas", ["composition", "lighting", "color", "movement"])
    if not isinstance(focus_areas, list):
        focus_areas = ["composition", "lighting", "color", "movement"]
    focus_areas = [_sanitize_text(str(a), 30, "focus_area") for a in focus_areas[:10]]
    
    model = _validate_enum(params.get("model", "gemini-2.5-flash"), ALLOWED_MODELS, "model", "gemini-2.5-flash")
    
    user_prompt = f"""Analyze this video reference:

Description: {description}
Focus Areas: {', '.join(focus_areas)}

Provide detailed analysis of the cinematic techniques used.
"""

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=REFERENCE_ANALYZER_SYSTEM,
            api_key=user_api_key,
            model=model,
        )
        
        return {
            "success": "error" not in result,
            "capsule_id": TeachingCapsuleId.REFERENCE_ANALYZE.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": TeachingCapsuleId.REFERENCE_ANALYZE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


# ============================================================================
# Main Entry Point
# ============================================================================

TEACHING_ADAPTERS: Dict[str, Callable] = {
    TeachingCapsuleId.PROMPT_GENERATE.value: run_prompt_generator,
    TeachingCapsuleId.STORYBOARD_CREATE.value: run_storyboard_creator,
    TeachingCapsuleId.IMAGE_GENERATE.value: run_image_generator,
    TeachingCapsuleId.REFERENCE_ANALYZE.value: run_reference_analyzer,
}


async def execute_teaching_capsule(
    capsule_id: str,
    inputs: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Execute a teaching capsule.
    
    Args:
        capsule_id: Capsule identifier (e.g., "teaching.prompt.generate")
        inputs: Input data for the capsule
        params: Optional parameters (model, etc.)
        user_api_key: Optional user API key for BYOK mode
    
    Returns:
        CapsuleResult with success status, output, and metrics
    """
    params = params or {}
    
    # Validate capsule_id
    adapter = TEACHING_ADAPTERS.get(capsule_id)
    if not adapter:
        valid_ids = [e.value for e in TeachingCapsuleId]
        return {
            "success": False,
            "capsule_id": capsule_id,
            "output": {},
            "error": f"Unknown capsule: {capsule_id}. Valid: {valid_ids}",
            "metrics": None,
        }
    
    logger.info(f"Executing teaching capsule: {capsule_id}")
    
    try:
        result = await adapter(inputs, params, user_api_key)
        
        if result["success"]:
            logger.info(f"Capsule {capsule_id} completed in {result.get('metrics', {}).get('latency_ms', '?')}ms")
        else:
            logger.warning(f"Capsule {capsule_id} failed: {result.get('error')}")
        
        return result
    except Exception as e:
        logger.exception(f"Unexpected error in capsule {capsule_id}")
        return {
            "success": False,
            "capsule_id": capsule_id,
            "output": {},
            "error": f"Internal error: {type(e).__name__}",
            "metrics": None,
        }
