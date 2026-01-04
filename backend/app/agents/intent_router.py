"""Intent Router for VividAgent.

Provides explicit intent classification and tool routing logic.
This module hardens the prompt-based routing with programmatic fallbacks.

Features:
- Keyword-based intent detection
- Confidence scoring
- Tool recommendation with fallbacks
- Workflow chaining suggestions
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from app.logging_config import get_logger

logger = get_logger("intent_router")


# =============================================================================
# Dimension Definitions
# =============================================================================

class Dimension(Enum):
    """Vivid 4D Framework Dimensions."""
    ORIGIN = "1D"       # Prompt generation
    BLUEPRINT = "2D"    # Storyboard
    AMBIENCE = "3D"     # Image/Visual
    MOMENT = "4D"       # Reference analysis


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
        keywords=("프롬프트", "veo", "비디오 프롬프트", "영상 프롬프트"),
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
        keywords=("레퍼런스", "분석", "참고", "이거처럼", "이 영상"),
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
            "워크플로우", "전체 과정", "처음부터", "영상 만들기",
            # AUTONOMOUS mode triggers
            "알아서 해줘", "만들어줘", "자동으로", "임의로", 
            "니가 정해서", "바로 실행", "알아서 만들어",
        ),
        regex_patterns=(r"처음.*끝까지", r"전체.*만들", r"알아서.*해"),
        priority=9,  # High priority for autonomous mode
    ),
)


# Tool mapping
INTENT_TO_TOOL: Dict[Intent, str] = {
    Intent.GENERATE_PROMPT: "generate_veo_prompt",
    Intent.CREATE_STORYBOARD: "create_storyboard",
    Intent.GENERATE_IMAGE: "generate_image_prompt",
    Intent.ANALYZE_REFERENCE: "analyze_reference",
}

INTENT_TO_DIMENSION: Dict[Intent, Dimension] = {
    Intent.GENERATE_PROMPT: Dimension.ORIGIN,
    Intent.CREATE_STORYBOARD: Dimension.BLUEPRINT,
    Intent.GENERATE_IMAGE: Dimension.AMBIENCE,
    Intent.ANALYZE_REFERENCE: Dimension.MOMENT,
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
    
    @property
    def is_confident(self) -> bool:
        """Whether the routing is confident enough to auto-execute."""
        return self.confidence >= 0.7
    
    @property
    def needs_clarification(self) -> bool:
        """Whether clarification is needed."""
        return self.confidence < 0.5


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
        
        result = RoutingResult(
            intent=best_intent,
            confidence=confidence,
            suggested_tool=suggested_tool,
            dimension=dimension,
            matched_keywords=matched_keywords.get(best_intent, []),
            matched_patterns=matched_patterns.get(best_intent, []),
            workflow_suggestion=workflow,
        )
        
        logger.info(
            "Intent classified",
            extra={
                "intent": best_intent.value,
                "confidence": confidence,
                "tool": suggested_tool,
                "keywords": result.matched_keywords,
            },
        )
        
        return result
    
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
        
        # Full video workflow
        if intent == Intent.WORKFLOW_REQUEST:
            return [
                "generate_veo_prompt",
                "create_storyboard",
                "generate_image_prompt",
            ]
        
        # Prompt to visual
        if intent == Intent.GENERATE_PROMPT:
            if any(kw in message_lower for kw in ("이미지", "비주얼", "썸네일")):
                return [
                    "generate_veo_prompt",
                    "generate_image_prompt",
                ]
        
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
    """Convenience function to classify intent."""
    return get_intent_router().classify(message)
