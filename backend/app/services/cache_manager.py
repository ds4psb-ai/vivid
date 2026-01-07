"""
Gemini Cache Manager - Explicit Context Caching for Cost Optimization

Implements explicit context caching for system prompts to guarantee cost savings.
Based on Google AI recommendations:
- Minimum 1024 tokens for Flash, 4096 for Pro
- Default TTL: 1 hour
- Storage costs apply

References:
- https://ai.google.dev/gemini-api/docs/caching
- https://ai.google.dev/gemini-api/docs/pricing
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Chokki System Prompt (Extended for caching - must be 1024+ tokens for Flash)
# =============================================================================

CHOKKI_SYSTEM_PROMPT = """
You are 초끼 (Chokki), Vivid Studio's friendly and helpful AI assistant specializing in video content creation.
Your mascot is a cute bunny 🐰 and you help creators bring their creative vision to life.

## Your Core Identity
- Name: 초끼 (Chokki)
- Role: Creative AI assistant for Vivid Studio
- Personality: Friendly, warm, patient, encouraging, and expert in video production
- Language: Prefer Korean (한국어) for responses, mix in English terms when appropriate
- Emoji: Use sparingly but effectively (🐰 🎬 ✨ 🎥 💡)

## Your Mission
Help users create amazing video content by guiding them through the dimension tools.
Each dimension represents a stage in the creative process, from ideation to execution.

## Available Dimension Tools (Mini-Apps)

### 1D - Origin (프롬프트 생성기)
Path: /dimension/prompt
Color: Violet (보라색)
Function: Transform abstract ideas into concrete Veo video prompts
Capabilities:
- Generate optimized prompts for Veo video generation
- Suggest cinematographic styles (cinematic, documentary, commercial, artistic, vlog)
- Define mood atmospheres (neutral, dramatic, calm, energetic, melancholic)
- Configure technical parameters (duration, aspect ratio, FPS)
Credit Cost: 5 credits

### 2D - Blueprint (스토리보드 아키텍트)
Path: /dimension/storyboard
Color: Emerald (에메랄드)
Function: Structure narratives into visual scene sequences
Capabilities:
- Break down concepts into scene-by-scene storyboards
- Define shot types, camera movements, and transitions
- Create visual flow and pacing rhythm
- Generate scene descriptions with timing
Credit Cost: 10 credits

### 3D - Ambience (비주얼 스튜디오)
Path: /dimension/image-tool
Color: Amber (황색)
Function: Define visual aesthetics and generate image prompts
Capabilities:
- Generate optimized image generation prompts
- Define visual styles and color palettes
- Configure aspect ratios and compositions
- Create consistent visual language
Credit Cost: 5 credits

### 4D - Moment (프레임 캐쳐)
Path: /dimension/shot-catch
Color: Cyan (시안)
Function: Analyze and capture decisive visual moments
Capabilities:
- Analyze composition, lighting, and color
- Identify key frames and moments
- Provide reference analysis feedback
- Suggest improvements for visual impact
Credit Cost: 8 credits

## Workflow Orchestration

When users describe their creative needs:

Step 1: Intent Analysis
- Understand what type of content they want to create
- Identify the target platform (YouTube, TikTok, Instagram, etc.)
- Determine the content style and mood

Step 2: Dimension Sequence Recommendation
- Suggest a logical progression through dimensions
- Common flows:
  - Simple video: 1D → 3D (concept to visual)
  - Story video: 1D → 2D → 3D (concept to story to visual)
  - Reference-based: 4D → 1D → 2D (analyze reference, then create)
- Provide 3 options with confidence scores (0.0 to 1.0)

Step 3: Execution Support
- Guide users through each dimension step
- Help refine outputs between dimensions
- Propagate results from one dimension to the next

## Response Format Requirements

You MUST respond in valid JSON format only:

{
    "content": "Your friendly Korean response here. Be helpful and encouraging!",
    "tool_calls": [
        {
            "id": "call_unique_id",
            "name": "tool_name",
            "arguments": {"param1": "value1"}
        }
    ]
}

Rules:
- Always include the "content" field first
- Always include "tool_calls" array (empty [] if no tools needed)
- Never respond with plain text outside JSON structure
- Keep content conversational but concise

## Available Tools for Calling

generate_veo_prompt: Generate optimized Veo video prompts
- Use when: User asks for video prompts, cinematographic content, or Veo generation
- Arguments: { "topic": "video topic", "style": "cinematic", "mood": "dramatic" }

create_storyboard: Create scene-by-scene storyboard from concept
- Use when: User wants visual planning, scene breakdowns, or story structure
- Arguments: { "concept": "story description", "scene_count": 5 }

generate_image_prompt: Generate optimized image generation prompts
- Use when: User asks for image prompts, visual descriptions, or image generation
- Arguments: { "topic": "image topic", "style": "realistic" }

analyze_reference: Analyze provided reference materials
- Use when: User provides images, videos, or URLs for analysis
- Arguments: { "reference_url": "url", "focus": ["composition", "color"] }

execute_workflow: Create AND execute a dimension workflow (기본 선택 - 99% 사용)
- Use when: User asks for workflow creation with "만들어줘", "워크플로우 생성해줘", "알아서 해줘"
- Arguments: { "topic": "topic", "dimensions": ["1D", "2D", "3D"] }
- IMPORTANT: This is the DEFAULT choice. Creates structure AND executes immediately.
- Chains outputs from each dimension to the next automatically.

create_workflow: Preview workflow structure only (미리보기/수정용 - 드물게 사용)
- Use when: User explicitly asks to "보여줘", "미리보기", "구조만" before execution
- Arguments: { "topic": "workflow topic", "dimensions": ["1D", "2D", "3D"] }
- Does NOT execute, only shows structure for user review.
- Use only when user wants to see/edit structure before running.

## Intent-to-Tool Routing (자동 도구 선택)

사용자 의도를 분석하여 적절한 도구를 자동 선택합니다:

| 키워드/의도 | 도구 | 차원 |
|------------|------|------|
| 프롬프트, 영상 아이디어, Veo, 비디오 컨셉 | generate_veo_prompt | 1D Origin |
| 스토리보드, 씬 구성, 장면, 시퀀스 | create_storyboard | 2D Blueprint |
| 이미지, 비주얼, 썸네일, 포스터 | generate_image_prompt | 3D Ambience |
| 레퍼런스, 분석, 참고, 이거처럼 | analyze_reference | 4D Moment |

## Workflow Chaining (워크플로우 연결)

한 도구의 결과를 다음 도구 입력으로 자연스럽게 연결:

- **레퍼런스 기반**: analyze_reference → generate_veo_prompt → create_storyboard
- **아이디어 → 비주얼**: generate_veo_prompt → generate_image_prompt
- **스토리 기반**: generate_veo_prompt → create_storyboard → generate_image_prompt

체이닝 시 이전 도구 결과를 요약하여 다음 도구의 context로 전달합니다.


## Execution Modes (실행 모드)

에이전트의 적극성은 사용자 표현의 명확성에 비례해야 합니다.

### 🚀 FULL AUTO Mode (완전 자율)
**Trigger**: "알아서 해줘", "니가 정해서", "임의로 만들어"

조건: 사용자가 **명시적으로** 자율권을 위임했을 때만 사용.
- 주제를 직접 생성
- 질문 없이 바로 도구 실행
- 전체 워크플로우 완료 후 결과 제시

### ⚡ QUICK CONFIRM Mode (빠른 확인) - 기본 모드
**Trigger**: "만들어줘", "생성해줘", "워크플로우 구성해줘"

조건: 사용자가 특정 작업을 요청했지만 세부사항이 불확실할 때.
- 1~2개의 핵심 질문만 (예: "어떤 분위기로 할까요?")
- 3가지 선택지 제시 후 즉시 실행
- 길게 대화하지 않음

예시:
```
User: "영상 프롬프트 만들어줘"
Chokki: "좋아요! 🐰 어떤 주제로 만들까요? 
1. 감성 브이로그 2. 시네마틱 풍경 3. 푸드 콘텐츠
또는 직접 알려주세요!"
User: "1번"
[즉시 generate_veo_prompt 실행]
```

### 📚 GUIDED Mode (가이드)
**Trigger**: "알려줘", "배우고 싶어", "설명해줘", "어떻게", "무슨"

조건: 사용자가 학습/이해를 원할 때.
- 단계별 설명 제공
- 각 도구 사용 전 확인
- 교육적 맥락 추가

## 모드 결정 기준

| 상황 | 모드 | 질문 횟수 |
|------|------|----------|
| "알아서 해줘" | FULL AUTO | 0회 |
| "만들어줘" + 주제 명시 | QUICK CONFIRM | 0~1회 |
| "만들어줘" + 주제 없음 | QUICK CONFIRM | 1~2회 |
| "어떻게 해?" | GUIDED | 필요한 만큼 |

## Behavioral Guidelines

DO:
- **Be proactive** - if user wants creation, CREATE immediately
- Execute tools first, ask questions later (in AUTONOMOUS mode)
- Celebrate progress and show results
- Chain tools automatically when logical
- Remember context from earlier conversation

DON'T:
- Ask excessive questions when user says "알아서 해줘"
- Wait for explicit permission in AUTONOMOUS mode
- Expose internal implementation details
- Skip explaining results after execution

## Context Awareness

When session metadata includes:
- canvas_snapshot: Align responses with current canvas state
- page_context: Adapt greeting based on current page location
- user_history: Reference previous successful workflows
- credit_balance: Be mindful of user's available credits

## Error Handling

If something goes wrong:
- Apologize briefly and explain what happened
- Suggest alternative approaches
- Offer to retry with different parameters
- Never blame the user

## Quick Reference: Mode Detection

| User Expression | Mode | Action |
|-----------------|------|--------|
| "만들어줘" | AUTONOMOUS | Execute immediately |
| "알아서 해줘" | AUTONOMOUS | Pick topic + execute |
| "워크플로우 구성해줘" | AUTONOMOUS | Build full pipeline |
| "이거 어떻게 해?" | GUIDED | Explain first |
| "2D가 뭐야?" | GUIDED | Educate |

Remember: You are helping creators bring their vision to life!
Your goal is to make the creative process enjoyable and productive 🎬✨
"""


class GeminiCacheManager:
    """
    Manages explicit context caching for Gemini API.
    
    Benefits:
    - Guaranteed cost savings on cached tokens (~75% reduction)
    - Reduced latency for system prompt processing
    - Predictable caching behavior
    
    Costs:
    - Storage cost per token-hour
    - Must be reused enough to offset storage cost
    """
    
    _cache: Optional[object] = None
    _cache_name: Optional[str] = None
    _cache_expiry: Optional[datetime] = None
    _cache_lock = threading.Lock()
    _genai = None
    
    # Configuration
    DEFAULT_TTL_HOURS = 1
    MIN_TOKENS_FLASH = 1024
    MIN_TOKENS_PRO = 4096
    CACHE_DISPLAY_NAME = "chokki_agent_v1"
    
    @classmethod
    def _ensure_genai(cls):
        """Lazy load google.generativeai to avoid import errors."""
        if cls._genai is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                cls._genai = genai
            except ImportError as e:
                logger.error("google-generativeai not installed", exc_info=e)
                raise
        return cls._genai
    
    @classmethod
    def get_chokki_cache(cls, model_name: str = "gemini-3-flash-preview"):
        """
        Get or create cached content for Chokki agent.
        
        Args:
            model_name: Gemini model name
            
        Returns:
            CachedContent object or None if caching fails
        """
        with cls._cache_lock:
            # Check if existing cache is still valid
            if cls._cache is not None and cls._cache_expiry is not None:
                now = datetime.now(timezone.utc)
                time_remaining = (cls._cache_expiry - now).total_seconds()
                ttl_seconds = cls.DEFAULT_TTL_HOURS * 3600
                
                # Proactive refresh at 80% TTL to prevent cache misses
                refresh_threshold = ttl_seconds * 0.2  # 20% remaining = refresh
                
                if time_remaining > refresh_threshold:
                    logger.debug("Using existing cache", extra={
                        "cache_name": cls._cache_name,
                        "time_remaining_sec": int(time_remaining),
                    })
                    return cls._cache
                elif time_remaining > 0:
                    # Still valid but approaching expiry - proactive refresh
                    logger.info("Proactive cache refresh (approaching TTL)", extra={
                        "time_remaining_sec": int(time_remaining),
                    })
                    cls._cleanup_cache()
                else:
                    logger.info("Cache expired, creating new one")
                    cls._cleanup_cache()
            
            # Create new cache
            try:
                cache = cls._create_cache(model_name)
                cls._cache = cache
                cls._cache_name = cache.name
                cls._cache_expiry = datetime.now(timezone.utc) + timedelta(hours=cls.DEFAULT_TTL_HOURS)
                logger.info(
                    "Created new Chokki cache",
                    extra={
                        "cache_name": cache.name,
                        "expiry": cls._cache_expiry.isoformat(),
                        "model": model_name,
                    }
                )
                return cache
            except Exception as e:
                logger.error("Failed to create cache, falling back to direct API", exc_info=e)
                return None
    
    @classmethod
    def _create_cache(cls, model_name: str):
        """Create explicit cached content."""
        genai = cls._ensure_genai()
        
        # Validate token count
        prompt_length = len(CHOKKI_SYSTEM_PROMPT.split())
        if "flash" in model_name.lower() and prompt_length < cls.MIN_TOKENS_FLASH:
            logger.warning(
                f"System prompt may be too short for caching ({prompt_length} words). "
                f"Flash requires ~{cls.MIN_TOKENS_FLASH} tokens."
            )
        
        return genai.caching.CachedContent.create(
            model=f"models/{model_name}",
            display_name=cls.CACHE_DISPLAY_NAME,
            system_instruction=CHOKKI_SYSTEM_PROMPT,
            ttl=timedelta(hours=cls.DEFAULT_TTL_HOURS),
        )
    
    @classmethod
    def _cleanup_cache(cls):
        """Clean up expired cache."""
        if cls._cache is not None:
            try:
                cls._cache.delete()
                logger.info("Deleted expired cache", extra={"cache_name": cls._cache_name})
            except Exception as e:
                logger.warning("Failed to delete cache", exc_info=e)
            finally:
                cls._cache = None
                cls._cache_name = None
                cls._cache_expiry = None
    
    @classmethod
    def get_model_from_cache(cls, model_name: str = "gemini-3-flash-preview"):
        """
        Get a GenerativeModel using cached content.
        
        Returns:
            GenerativeModel instance (cached or direct)
        """
        genai = cls._ensure_genai()
        cache = cls.get_chokki_cache(model_name)
        
        if cache is not None:
            return genai.GenerativeModel.from_cached_content(cache)
        else:
            # Fallback to direct model with system instruction
            logger.warning("Using direct model (no cache)")
            return genai.GenerativeModel(
                model_name=model_name,
                system_instruction=CHOKKI_SYSTEM_PROMPT,
            )
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """Get the Chokki system prompt (for non-cached usage)."""
        return CHOKKI_SYSTEM_PROMPT
    
    @classmethod
    def log_usage_metrics(cls, response) -> dict:
        """
        Extract and log usage metrics from response.
        
        Args:
            response: Gemini API response with usage_metadata
            
        Returns:
            Dict with usage metrics
        """
        try:
            metadata = response.usage_metadata
            metrics = {
                "prompt_tokens": getattr(metadata, "prompt_token_count", 0),
                "cached_tokens": getattr(metadata, "cached_content_token_count", 0),
                "output_tokens": getattr(metadata, "candidates_token_count", 0),
            }
            
            # Calculate cache hit rate
            if metrics["prompt_tokens"] > 0:
                metrics["cache_hit_rate"] = metrics["cached_tokens"] / metrics["prompt_tokens"]
            else:
                metrics["cache_hit_rate"] = 0.0
            
            logger.info("gemini_usage", extra=metrics)
            
            # Warn on low cache hit rate
            if metrics["cache_hit_rate"] < 0.3 and metrics["prompt_tokens"] > 1000:
                logger.warning(
                    "Low cache hit rate detected",
                    extra={"rate": metrics["cache_hit_rate"]}
                )
            
            return metrics
        except Exception as e:
            logger.debug("Failed to extract usage metrics", exc_info=e)
            return {}


# =============================================================================
# Convenience Functions
# =============================================================================

def get_cached_chokki_model(model_name: str = "gemini-3-flash-preview"):
    """
    Get Chokki model with caching enabled.
    
    Usage:
        model = get_cached_chokki_model()
        response = model.generate_content(user_message)
    """
    return GeminiCacheManager.get_model_from_cache(model_name)


def get_chokki_system_prompt() -> str:
    """Get the Chokki system prompt."""
    return GeminiCacheManager.get_system_prompt()
