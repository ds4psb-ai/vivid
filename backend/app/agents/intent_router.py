"""Intent Router for VividAgent.

Provides explicit intent classification and tool routing logic.
This module hardens the prompt-based routing with programmatic fallbacks.

P1-2 Enhanced Features:
- Keyword-based intent detection (primary)
- LLM-based fallback for low-confidence cases
- Classification result caching (TTL 5 min)
- Hybrid confidence scoring
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from cachetools import TTLCache

from app.logging_config import get_logger

logger = get_logger("intent_router")

# P1-2: Classification cache (max 500 entries, 5 min TTL)
_CLASSIFICATION_CACHE: TTLCache = TTLCache(maxsize=500, ttl=300)

# P1-2: LLM classification thresholds
LLM_FALLBACK_THRESHOLD = 0.6  # Use LLM if keyword confidence < this
LLM_MIN_MESSAGE_LENGTH = 15    # Only use LLM for messages longer than this


# =============================================================================
# Dimension Definitions
# =============================================================================

class Dimension(Enum):
    """Vivid 4D Framework Dimensions + Extended Capsules."""
    ORIGIN = "1D"       # Prompt generation
    BLUEPRINT = "2D"    # Storyboard
    AMBIENCE = "3D"     # Image/Visual
    MOMENT = "4D"       # Reference analysis
    # Extended Dimension Capsules
    QUALITY = "QC"      # Quality Check
    AESTHETIC = "AD"    # Aesthetic Director
    ABYSS = "AI"        # Abyss Interpreter (Persona Analyze)
    VIDEO = "VEO"       # Veo Video Generate


# =============================================================================
# Intent Classification
# =============================================================================

class Intent(Enum):
    """User intent categories."""
    GENERATE_PROMPT = "generate_prompt"
    CREATE_STORYBOARD = "create_storyboard"
    GENERATE_IMAGE = "generate_image"
    ANALYZE_REFERENCE = "analyze_reference"
    GENERAL_CHAT = "general_chat"
    WORKFLOW_REQUEST = "workflow_request"
    UNKNOWN = "unknown"
    # Extended Dimension Capsule Intents
    QUALITY_CHECK = "quality_check"
    AESTHETIC_DIRECT = "aesthetic_direct"
    PERSONA_ANALYZE = "persona_analyze"
    VEO_GENERATE = "veo_generate"


@dataclass(frozen=True)
class IntentPattern:
    """Pattern for intent detection."""
    intent: Intent
    keywords: Tuple[str, ...]
    regex_patterns: Tuple[str, ...] = field(default_factory=tuple)
    priority: int = 0  # Higher = more specific


# Intent patterns - ordered by priority
INTENT_PATTERNS: Tuple[IntentPattern, ...] = (
    # High priority - explicit tool mentions
    IntentPattern(
        intent=Intent.GENERATE_PROMPT,
        keywords=("프롬프트", "veo", "비디오 프롬프트", "영상 프롬프트", "트렌드", "trend", "prompt", "idea"),
        regex_patterns=(r"프롬프트.*생성", r"veo.*만들"),
        priority=10,
    ),
    IntentPattern(
        intent=Intent.CREATE_STORYBOARD,
        keywords=("스토리보드", "씬 구성", "장면 구성", "시퀀스"),
        regex_patterns=(r"스토리보드.*만들", r"씬.*나누"),
        priority=10,
    ),
    IntentPattern(
        intent=Intent.GENERATE_IMAGE,
        keywords=("이미지 프롬프트", "비주얼", "썸네일", "포스터"),
        regex_patterns=(r"이미지.*생성", r"비주얼.*만들"),
        priority=10,
    ),
    IntentPattern(
        intent=Intent.ANALYZE_REFERENCE,
        keywords=("레퍼런스", "분석", "참고", "이거처럼", "이 영상", "analyze", "reference"),
        regex_patterns=(r"분석.*해", r"레퍼런스.*봐", r"이거.*처럼"),
        priority=10,
    ),
    
    # Medium priority - content type mentions
    IntentPattern(
        intent=Intent.GENERATE_PROMPT,
        keywords=("영상 아이디어", "비디오 컨셉", "영상 컨셉", "유튜브 영상"),
        priority=5,
    ),
    IntentPattern(
        intent=Intent.CREATE_STORYBOARD,
        keywords=("장면", "컷", "시나리오"),
        priority=5,
    ),
    IntentPattern(
        intent=Intent.GENERATE_IMAGE,
        keywords=("이미지", "그림", "사진"),
        priority=5,
    ),
    
    # Workflow requests (including AUTONOMOUS mode triggers)
    IntentPattern(
        intent=Intent.WORKFLOW_REQUEST,
        keywords=(
            "워크플로우", "전체 과정", "처음부터", "영상 만들기", "workflow", "script", "스크립트",
            # AUTONOMOUS mode triggers
            "알아서 해줘", "만들어줘", "자동으로", "임의로",
            "니가 정해서", "바로 실행", "알아서 만들어",
        ),
        regex_patterns=(r"처음.*끝까지", r"전체.*만들", r"알아서.*해"),
        priority=9,  # High priority for autonomous mode
    ),

    # Extended Dimension Capsule Patterns
    # QC - Quality Check
    IntentPattern(
        intent=Intent.QUALITY_CHECK,
        keywords=("검수", "품질", "검사", "평가", "퀄리티", "품질 확인", "적합성"),
        regex_patterns=(r"품질.*확인", r"검수.*해", r"적합성.*검사", r"퀄리티.*체크"),
        priority=8,
    ),
    # AD - Aesthetic Director
    IntentPattern(
        intent=Intent.AESTHETIC_DIRECT,
        keywords=("미학", "스타일 가이드", "비주얼 가이드", "감독 스타일", "미적", "색감", "톤앤매너"),
        regex_patterns=(r"스타일.*가이드", r"미학.*정의", r"시각.*스타일", r"감독.*스타일"),
        priority=8,
    ),
    # AI - Abyss Interpreter (Persona Analyze)
    IntentPattern(
        intent=Intent.PERSONA_ANALYZE,
        keywords=("페르소나", "심연", "성향 분석", "심층 분석", "성격 분석", "캐릭터 분석", "사주", "운명"),
        regex_patterns=(r"페르소나.*분석", r"심층.*분석", r"성향.*알려", r"나.*분석"),
        priority=8,
    ),
    # VEO - Veo Video Generate
    IntentPattern(
        intent=Intent.VEO_GENERATE,
        keywords=("비디오 생성", "영상 생성", "동영상 만들", "veo 생성", "최종 영상", "비디오 제작"),
        regex_patterns=(r"비디오.*만들", r"영상.*생성", r"동영상.*제작", r"veo.*생성"),
        priority=8,
    ),
)


# Tool mapping
INTENT_TO_TOOL: Dict[Intent, str] = {
    Intent.GENERATE_PROMPT: "generate_veo_prompt",
    Intent.CREATE_STORYBOARD: "create_storyboard",
    Intent.GENERATE_IMAGE: "generate_image_prompt",
    Intent.ANALYZE_REFERENCE: "analyze_reference",
    # Extended Dimension Capsules
    Intent.QUALITY_CHECK: "quality_check",
    Intent.AESTHETIC_DIRECT: "aesthetic_direct",
    Intent.PERSONA_ANALYZE: "persona_analyze",
    Intent.VEO_GENERATE: "veo_generate",
}

INTENT_TO_DIMENSION: Dict[Intent, Dimension] = {
    Intent.GENERATE_PROMPT: Dimension.ORIGIN,
    Intent.CREATE_STORYBOARD: Dimension.BLUEPRINT,
    Intent.GENERATE_IMAGE: Dimension.AMBIENCE,
    Intent.ANALYZE_REFERENCE: Dimension.MOMENT,
    # Extended Dimension Capsules
    Intent.QUALITY_CHECK: Dimension.QUALITY,
    Intent.AESTHETIC_DIRECT: Dimension.AESTHETIC,
    Intent.PERSONA_ANALYZE: Dimension.ABYSS,
    Intent.VEO_GENERATE: Dimension.VIDEO,
}


# =============================================================================
# Intent Router
# =============================================================================

@dataclass
class RoutingResult:
    """Result of intent routing."""
    intent: Intent
    confidence: float  # 0.0 - 1.0
    suggested_tool: Optional[str]
    dimension: Optional[Dimension]
    matched_keywords: List[str]
    matched_patterns: List[str]
    workflow_suggestion: Optional[List[str]] = None
    auto_execute: bool = False  # True for AUTONOMOUS mode ("알아서 해줘")
    full_workflow: bool = False  # True for "전체 워크플로우" requests

    @property
    def is_confident(self) -> bool:
        """Whether the routing is confident enough to auto-execute."""
        return self.confidence >= 0.7

    @property
    def needs_clarification(self) -> bool:
        """Whether clarification is needed."""
        return self.confidence < 0.5

    @property
    def should_auto_execute(self) -> bool:
        """Whether to trigger automatic workflow execution."""
        return self.auto_execute and self.is_confident

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for caching."""
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "suggested_tool": self.suggested_tool,
            "dimension": self.dimension.value if self.dimension else None,
            "matched_keywords": self.matched_keywords,
            "matched_patterns": self.matched_patterns,
            "workflow_suggestion": self.workflow_suggestion,
            "auto_execute": self.auto_execute,
            "full_workflow": self.full_workflow,
        }


class IntentRouter:
    """Routes user intent to appropriate tools."""
    
    def __init__(self) -> None:
        self._patterns = INTENT_PATTERNS
        self._compiled_regex: Dict[str, re.Pattern] = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns."""
        for pattern in self._patterns:
            for regex in pattern.regex_patterns:
                if regex not in self._compiled_regex:
                    try:
                        self._compiled_regex[regex] = re.compile(regex, re.IGNORECASE)
                    except re.error as e:
                        logger.warning(f"Invalid regex pattern: {regex}", extra={"error": str(e)})
    
    def classify(self, user_message: str) -> RoutingResult:
        """
        Classify user intent from message.
        
        Args:
            user_message: User's input message
            
        Returns:
            RoutingResult with intent, confidence, and suggestions
        """
        if not user_message or not user_message.strip():
            return RoutingResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                suggested_tool=None,
                dimension=None,
                matched_keywords=[],
                matched_patterns=[],
            )
        
        message_lower = user_message.lower()
        
        # Score each intent
        intent_scores: Dict[Intent, float] = {}
        matched_keywords: Dict[Intent, List[str]] = {}
        matched_patterns: Dict[Intent, List[str]] = {}
        
        for pattern in self._patterns:
            score = 0.0
            keywords_found = []
            patterns_found = []
            
            # Check keywords
            for keyword in pattern.keywords:
                if keyword.lower() in message_lower:
                    score += 1.0
                    keywords_found.append(keyword)
            
            # Check regex patterns
            for regex_str in pattern.regex_patterns:
                compiled = self._compiled_regex.get(regex_str)
                if compiled and compiled.search(message_lower):
                    score += 1.5  # Regex matches are more specific
                    patterns_found.append(regex_str)
            
            # Apply priority boost
            if score > 0:
                score += pattern.priority * 0.1
            
            # Accumulate for this intent
            if score > 0:
                current = intent_scores.get(pattern.intent, 0)
                intent_scores[pattern.intent] = current + score
                
                if pattern.intent not in matched_keywords:
                    matched_keywords[pattern.intent] = []
                    matched_patterns[pattern.intent] = []
                matched_keywords[pattern.intent].extend(keywords_found)
                matched_patterns[pattern.intent].extend(patterns_found)
        
        # Find best intent
        if not intent_scores:
            return RoutingResult(
                intent=Intent.GENERAL_CHAT,
                confidence=0.3,
                suggested_tool=None,
                dimension=None,
                matched_keywords=[],
                matched_patterns=[],
            )
        
        best_intent = max(intent_scores, key=intent_scores.get)  # type: ignore
        best_score = intent_scores[best_intent]
        
        # Normalize confidence (cap at 1.0)
        confidence = min(best_score / 5.0, 1.0)
        
        # Get tool and dimension
        suggested_tool = INTENT_TO_TOOL.get(best_intent)
        dimension = INTENT_TO_DIMENSION.get(best_intent)
        
        # Generate workflow suggestion for complex requests
        workflow = self._suggest_workflow(best_intent, user_message)

        # AUTONOMOUS mode detection
        auto_execute = False
        full_workflow = False

        if best_intent == Intent.WORKFLOW_REQUEST:
            # Auto-execute triggers: 자동 실행 요청
            auto_triggers = (
                "알아서 해줘", "알아서 만들어", "만들어줘", "자동으로",
                "니가 정해서", "바로 실행", "임의로", "그냥 해줘",
            )
            if any(t in message_lower for t in auto_triggers):
                auto_execute = True

            # Full workflow triggers: 전체 워크플로우 요청
            full_triggers = (
                "전체", "처음부터", "끝까지", "8개", "모든 차원",
                "전부", "풀", "완전", "다 해줘",
            )
            if any(t in message_lower for t in full_triggers):
                full_workflow = True

        result = RoutingResult(
            intent=best_intent,
            confidence=confidence,
            suggested_tool=suggested_tool,
            dimension=dimension,
            matched_keywords=matched_keywords.get(best_intent, []),
            matched_patterns=matched_patterns.get(best_intent, []),
            workflow_suggestion=workflow,
            auto_execute=auto_execute,
            full_workflow=full_workflow,
        )

        logger.info(
            "Intent classified",
            extra={
                "intent": best_intent.value,
                "confidence": confidence,
                "tool": suggested_tool,
                "keywords": result.matched_keywords,
                "auto_execute": auto_execute,
                "full_workflow": full_workflow,
            },
        )

        return result
    
    def classify_with_llm_fallback(self, user_message: str) -> RoutingResult:
        """P1-2: Classify with LLM fallback for low-confidence cases.
        
        Uses keyword classification first, then falls back to LLM
        if confidence is below threshold.
        
        Args:
            user_message: User's input message
            
        Returns:
            RoutingResult with potentially improved confidence
        """
        # Check cache first
        cache_key = self._get_cache_key(user_message)
        cached = _CLASSIFICATION_CACHE.get(cache_key)
        if cached:
            logger.debug(f"Intent cache hit: {cache_key[:16]}...")
            return self._result_from_cache(cached)
        
        # Primary: keyword-based classification
        keyword_result = self.classify(user_message)
        
        # Check if LLM fallback is needed
        should_use_llm = (
            keyword_result.confidence < LLM_FALLBACK_THRESHOLD
            and len(user_message.strip()) >= LLM_MIN_MESSAGE_LENGTH
            and keyword_result.intent not in (Intent.GENERAL_CHAT, Intent.UNKNOWN)
        )
        
        if not should_use_llm:
            # Cache and return keyword result
            _CLASSIFICATION_CACHE[cache_key] = keyword_result.to_dict()
            return keyword_result
        
        # LLM fallback (sync wrapper for async call)
        try:
            llm_result = self._classify_with_llm_sync(user_message)
            if llm_result and llm_result.confidence > keyword_result.confidence:
                logger.info(
                    "LLM classification improved confidence",
                    extra={
                        "keyword_intent": keyword_result.intent.value,
                        "keyword_confidence": keyword_result.confidence,
                        "llm_intent": llm_result.intent.value,
                        "llm_confidence": llm_result.confidence,
                    }
                )
                # Merge workflow suggestions from keyword result
                if not llm_result.workflow_suggestion and keyword_result.workflow_suggestion:
                    llm_result = RoutingResult(
                        intent=llm_result.intent,
                        confidence=llm_result.confidence,
                        suggested_tool=llm_result.suggested_tool,
                        dimension=llm_result.dimension,
                        matched_keywords=keyword_result.matched_keywords,
                        matched_patterns=keyword_result.matched_patterns,
                        workflow_suggestion=keyword_result.workflow_suggestion,
                        auto_execute=keyword_result.auto_execute or llm_result.auto_execute,
                        full_workflow=keyword_result.full_workflow or llm_result.full_workflow,
                    )
                _CLASSIFICATION_CACHE[cache_key] = llm_result.to_dict()
                return llm_result
        except Exception as e:
            logger.warning(f"LLM classification failed, using keyword result: {e}")
        
        _CLASSIFICATION_CACHE[cache_key] = keyword_result.to_dict()
        return keyword_result
    
    def _get_cache_key(self, message: str) -> str:
        """Generate cache key from message."""
        normalized = message.strip().lower()[:200]  # Limit length for efficiency
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _result_from_cache(self, cached: Dict[str, Any]) -> RoutingResult:
        """Reconstruct RoutingResult from cached dict."""
        intent_str = cached.get("intent", "unknown")
        try:
            intent = Intent(intent_str)
        except ValueError:
            intent = Intent.UNKNOWN
        
        dimension_str = cached.get("dimension")
        dimension = None
        if dimension_str:
            try:
                dimension = Dimension(dimension_str)
            except ValueError:
                pass
        
        return RoutingResult(
            intent=intent,
            confidence=cached.get("confidence", 0.0),
            suggested_tool=cached.get("suggested_tool"),
            dimension=dimension,
            matched_keywords=cached.get("matched_keywords", []),
            matched_patterns=cached.get("matched_patterns", []),
            workflow_suggestion=cached.get("workflow_suggestion"),
            auto_execute=cached.get("auto_execute", False),
            full_workflow=cached.get("full_workflow", False),
        )
    
    def _classify_with_llm_sync(self, message: str) -> Optional[RoutingResult]:
        """Synchronous LLM classification using Gemini Flash.
        
        P1-2: Uses lightweight model for cost efficiency.
        """
        try:
            import google.generativeai as genai
            from app.config import settings
            
            if not settings.GEMINI_API_KEY:
                return None
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Use fast model for classification
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            # Build classification prompt
            prompt = f"""Classify the user intent for a video creation assistant.

User message: "{message[:300]}"

Intent categories:
- generate_prompt: Create video prompts for Veo
- create_storyboard: Design scene sequences
- generate_image: Create image prompts/thumbnails
- analyze_reference: Analyze reference videos/images
- quality_check: Review content quality
- aesthetic_direct: Style/aesthetic guidance
- persona_analyze: Character/persona analysis
- veo_generate: Generate actual video
- workflow_request: Full workflow execution
- general_chat: General conversation/questions

Respond with ONLY valid JSON:
{{"intent": "<category>", "confidence": <0.0-1.0>}}"""
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=100,
                )
            )
            
            # Parse response
            text = response.text.strip()
            # Extract JSON from response
            if "{" in text and "}" in text:
                json_start = text.index("{")
                json_end = text.rindex("}") + 1
                json_str = text[json_start:json_end]
                data = json.loads(json_str)
                
                intent_str = data.get("intent", "unknown")
                confidence = float(data.get("confidence", 0.5))
                
                try:
                    intent = Intent(intent_str)
                except ValueError:
                    intent = Intent.UNKNOWN
                    confidence = 0.3
                
                return RoutingResult(
                    intent=intent,
                    confidence=confidence,
                    suggested_tool=INTENT_TO_TOOL.get(intent),
                    dimension=INTENT_TO_DIMENSION.get(intent),
                    matched_keywords=[],
                    matched_patterns=["llm_classification"],
                    auto_execute=False,
                    full_workflow=False,
                )
                
        except ImportError:
            logger.debug("google-generativeai not installed")
        except Exception as e:
            logger.warning(f"LLM classification error: {e}")
        
        return None
    
    def _suggest_workflow(
        self,
        intent: Intent,
        message: str
    ) -> Optional[List[str]]:
        """Suggest a workflow based on intent and context."""
        message_lower = message.lower()

        # Reference-based workflow
        if intent == Intent.ANALYZE_REFERENCE:
            if any(kw in message_lower for kw in ("만들", "생성", "제작")):
                return [
                    "analyze_reference",
                    "generate_veo_prompt",
                    "create_storyboard",
                ]

        # Full video workflow - enhanced with optional QC/AD/VEO
        if intent == Intent.WORKFLOW_REQUEST:
            workflow = [
                "generate_veo_prompt",
                "create_storyboard",
                "generate_image_prompt",
            ]
            # Add aesthetic direction if style/aesthetic mentioned
            if any(kw in message_lower for kw in ("스타일", "미학", "감독", "톤", "색감")):
                workflow.insert(2, "aesthetic_direct")
            # Add quality check if mentioned
            if any(kw in message_lower for kw in ("검수", "품질", "검사", "퀄리티")):
                workflow.append("quality_check")
            # Add Veo video at end if video generation mentioned
            if any(kw in message_lower for kw in ("비디오", "영상 생성", "동영상", "veo")):
                workflow.append("veo_generate")
            return workflow

        # Prompt to visual
        if intent == Intent.GENERATE_PROMPT:
            if any(kw in message_lower for kw in ("이미지", "비주얼", "썸네일")):
                return [
                    "generate_veo_prompt",
                    "generate_image_prompt",
                ]

        # Quality Check: suggest after content generation
        if intent == Intent.QUALITY_CHECK:
            if any(kw in message_lower for kw in ("스토리보드", "프롬프트", "이미지")):
                return ["quality_check"]
            # If standalone, suggest common chain: create then check
            return ["create_storyboard", "quality_check"]

        # Aesthetic Director: suggest style guide workflow
        if intent == Intent.AESTHETIC_DIRECT:
            if any(kw in message_lower for kw in ("영상", "비디오", "프롬프트")):
                return ["aesthetic_direct", "generate_veo_prompt", "create_storyboard"]
            return ["aesthetic_direct"]

        # Persona Analyze: suggest persona-driven content workflow
        if intent == Intent.PERSONA_ANALYZE:
            if any(kw in message_lower for kw in ("콘텐츠", "영상", "프롬프트")):
                return ["persona_analyze", "generate_veo_prompt", "create_storyboard"]
            return ["persona_analyze"]

        # Veo Generate: suggest full pipeline to video
        if intent == Intent.VEO_GENERATE:
            if any(kw in message_lower for kw in ("처음", "전체", "프롬프트")):
                return ["generate_veo_prompt", "create_storyboard", "veo_generate"]
            return ["veo_generate"]

        return None
    
    def get_routing_context(self, result: RoutingResult) -> str:
        """
        Generate a routing context string for the system prompt.
        
        This can be injected into the agent context to guide tool selection.
        """
        if result.intent == Intent.GENERAL_CHAT:
            return ""
        
        lines = [
            f"[Routing Hint] Detected intent: {result.intent.value}",
            f"Confidence: {result.confidence:.2f}",
        ]
        
        if result.suggested_tool:
            lines.append(f"Suggested tool: {result.suggested_tool}")
        
        if result.dimension:
            lines.append(f"Dimension: {result.dimension.value}")
        
        if result.workflow_suggestion:
            lines.append(f"Suggested workflow: {' → '.join(result.workflow_suggestion)}")
        
        return "\n".join(lines)


# =============================================================================
# Singleton Instance
# =============================================================================

_router: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    """Get or create the singleton intent router."""
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router


def classify_intent(message: str) -> RoutingResult:
    """Convenience function to classify intent (keyword-only, fast)."""
    return get_intent_router().classify(message)


def classify_intent_hybrid(message: str) -> RoutingResult:
    """P1-2: Hybrid classification with LLM fallback for low-confidence.
    
    Use this for higher accuracy when latency tolerance allows.
    Falls back to LLM only when keyword confidence < 0.6.
    Results are cached for 5 minutes.
    """
    return get_intent_router().classify_with_llm_fallback(message)


def clear_classification_cache() -> None:
    """Clear the classification cache."""
    _CLASSIFICATION_CACHE.clear()
    logger.info("Classification cache cleared")


def get_cache_stats() -> Dict[str, int]:
    """Get classification cache statistics."""
    return {
        "size": len(_CLASSIFICATION_CACHE),
        "maxsize": _CLASSIFICATION_CACHE.maxsize,
        "ttl": int(_CLASSIFICATION_CACHE.ttl),
    }
