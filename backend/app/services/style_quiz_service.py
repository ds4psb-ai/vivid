"""Style Quiz Service - Gamified Quick Quiz for Creator DNA Matching.

P5: 30초 스타일 퀴즈로 거장 DNA 매칭

Based on PSYCHOGRAPHIC_UX_RESEARCH_2026.md Pattern C:
- 3-5 questions (10+ causes high dropout)
- Image comparison questions
- Instant results with auteur DNA matching
- Share button support

Usage:
    from app.services.style_quiz_service import (
        get_style_quiz_service,
        QuizQuestion,
        QuizResult,
    )

    service = get_style_quiz_service()

    # Get quiz questions
    questions = service.get_questions()

    # Submit answers and get DNA match
    result = service.calculate_result(answers)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class QuizDimension(str, Enum):
    """Quiz question dimensions for DNA matching."""
    VISUAL_STYLE = "visual_style"      # 시각적 스타일 선호
    NARRATIVE = "narrative"            # 내러티브 선호
    EMOTION = "emotion"                # 감정 표현 방식
    CREATIVE_GOAL = "creative_goal"    # 창작 목표
    PACING = "pacing"                  # 템포/페이싱


class AuteurKey(str, Enum):
    """Available auteur keys for DNA matching."""
    BONG = "bong"           # 봉준호 - 사회비평, 장르혼합
    WONG = "wong"           # 왕가위 - 네온, 감성
    KUBRICK = "kubrick"     # 큐브릭 - 대칭, 완벽주의
    NOLAN = "nolan"         # 놀란 - 시간, 구조
    VILLENEUVE = "villeneuve"  # 빌뇌브 - 스케일, 분위기
    TARANTINO = "tarantino"    # 타란티노 - 대화, 폭력미학
    FINCHER = "fincher"        # 핀처 - 어둠, 디테일
    WACHOWSKI = "wachowski"    # 워쇼스키 - SF, 철학


# Auteur profiles for matching
AUTEUR_PROFILES: Dict[str, Dict[str, Any]] = {
    "bong": {
        "name_ko": "봉준호",
        "name_en": "Bong Joon-ho",
        "signature": "사회비평 + 장르혼합",
        "visual_style": ["vertical_composition", "contrast", "realistic"],
        "narrative": ["social_critique", "twist", "dark_humor"],
        "emotion": ["tension", "satire", "empathy"],
        "pacing": ["deliberate", "building"],
        "creative_goal": ["message", "art"],
        "keywords": ["기생충", "괴물", "살인의 추억"],
    },
    "wong": {
        "name_ko": "왕가위",
        "name_en": "Wong Kar-wai",
        "signature": "네온 색감 + 감성적 서사",
        "visual_style": ["neon", "blur", "saturated"],
        "narrative": ["mood", "longing", "fragment"],
        "emotion": ["melancholy", "romantic", "nostalgic"],
        "pacing": ["slow", "dreamy"],
        "creative_goal": ["emotion", "beauty"],
        "keywords": ["화양연화", "중경삼림", "2046"],
    },
    "kubrick": {
        "name_ko": "스탠리 큐브릭",
        "name_en": "Stanley Kubrick",
        "signature": "대칭 구도 + 완벽주의",
        "visual_style": ["symmetry", "wide", "controlled"],
        "narrative": ["psychological", "dystopia", "adaptation"],
        "emotion": ["cold", "intellectual", "unsettling"],
        "pacing": ["methodical", "hypnotic"],
        "creative_goal": ["perfection", "art"],
        "keywords": ["샤이닝", "2001 스페이스 오디세이", "풀 메탈 재킷"],
    },
    "nolan": {
        "name_ko": "크리스토퍼 놀란",
        "name_en": "Christopher Nolan",
        "signature": "시간 조작 + 구조적 서사",
        "visual_style": ["imax", "practical", "grand"],
        "narrative": ["nonlinear", "puzzle", "time"],
        "emotion": ["epic", "cerebral", "intense"],
        "pacing": ["complex", "layered"],
        "creative_goal": ["innovation", "spectacle"],
        "keywords": ["인셉션", "인터스텔라", "테넷"],
    },
    "villeneuve": {
        "name_ko": "드니 빌뇌브",
        "name_en": "Denis Villeneuve",
        "signature": "스케일 + 철학적 분위기",
        "visual_style": ["vast", "atmospheric", "minimal"],
        "narrative": ["philosophical", "slow_burn", "existential"],
        "emotion": ["awe", "contemplative", "haunting"],
        "pacing": ["meditative", "immersive"],
        "creative_goal": ["art", "depth"],
        "keywords": ["블레이드 러너 2049", "듄", "어라이벌"],
    },
    "tarantino": {
        "name_ko": "쿠엔틴 타란티노",
        "name_en": "Quentin Tarantino",
        "signature": "대화 + 폭력 미학",
        "visual_style": ["retro", "stylized", "reference"],
        "narrative": ["dialogue", "nonlinear", "revenge"],
        "emotion": ["cool", "shocking", "witty"],
        "pacing": ["talky", "explosive"],
        "creative_goal": ["entertainment", "style"],
        "keywords": ["펄프 픽션", "킬 빌", "장고"],
    },
    "fincher": {
        "name_ko": "데이빗 핀처",
        "name_en": "David Fincher",
        "signature": "어둠 + 극도의 디테일",
        "visual_style": ["dark", "precise", "green_tint"],
        "narrative": ["thriller", "obsession", "mystery"],
        "emotion": ["dread", "paranoia", "clinical"],
        "pacing": ["relentless", "meticulous"],
        "creative_goal": ["perfection", "darkness"],
        "keywords": ["세븐", "파이트 클럽", "조디악"],
    },
    "wachowski": {
        "name_ko": "워쇼스키",
        "name_en": "The Wachowskis",
        "signature": "SF + 철학적 액션",
        "visual_style": ["futuristic", "bullet_time", "cyber"],
        "narrative": ["philosophical", "revolution", "identity"],
        "emotion": ["rebellious", "transcendent", "epic"],
        "pacing": ["action", "philosophical"],
        "creative_goal": ["innovation", "message"],
        "keywords": ["매트릭스", "클라우드 아틀라스", "센스8"],
    },
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class QuizOption:
    """A single option for a quiz question."""
    id: str
    text: str
    image_url: Optional[str] = None
    auteur_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class QuizQuestion:
    """A quiz question with options."""
    id: str
    dimension: QuizDimension
    question_ko: str
    question_en: str
    options: List[QuizOption]
    order: int = 0


@dataclass
class AuteurMatch:
    """A single auteur match result."""
    auteur_key: str
    name_ko: str
    name_en: str
    match_percentage: float
    signature: str
    keywords: List[str]


@dataclass
class QuizResult:
    """Complete quiz result with DNA matching."""
    success: bool
    primary_match: AuteurMatch
    secondary_matches: List[AuteurMatch]
    dimension_scores: Dict[str, str]  # dimension → dominant style
    creative_profile: Dict[str, Any]
    share_text: str
    evidence_refs: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ============================================================================
# Quiz Questions Definition
# ============================================================================

QUIZ_QUESTIONS: List[QuizQuestion] = [
    QuizQuestion(
        id="q1_visual",
        dimension=QuizDimension.VISUAL_STYLE,
        question_ko="이 두 장면 중 더 끌리는 것은?",
        question_en="Which scene appeals to you more?",
        order=1,
        options=[
            QuizOption(
                id="q1_a",
                text="수직 구도의 긴장감 있는 장면",
                image_url="/quiz/bong_vertical.jpg",
                auteur_weights={"bong": 1.0, "fincher": 0.5, "kubrick": 0.3},
            ),
            QuizOption(
                id="q1_b",
                text="네온 불빛의 감성적인 장면",
                image_url="/quiz/wong_neon.jpg",
                auteur_weights={"wong": 1.0, "villeneuve": 0.5, "wachowski": 0.3},
            ),
            QuizOption(
                id="q1_c",
                text="완벽한 대칭 구도의 장면",
                image_url="/quiz/kubrick_symmetry.jpg",
                auteur_weights={"kubrick": 1.0, "fincher": 0.5, "villeneuve": 0.3},
            ),
            QuizOption(
                id="q1_d",
                text="광활한 스케일의 장면",
                image_url="/quiz/villeneuve_scale.jpg",
                auteur_weights={"villeneuve": 1.0, "nolan": 0.7, "kubrick": 0.3},
            ),
        ],
    ),
    QuizQuestion(
        id="q2_narrative",
        dimension=QuizDimension.NARRATIVE,
        question_ko="영상에서 가장 중요한 요소는?",
        question_en="What's the most important element in a video?",
        order=2,
        options=[
            QuizOption(
                id="q2_a",
                text="사회적 메시지와 비평",
                auteur_weights={"bong": 1.0, "wachowski": 0.5, "nolan": 0.3},
            ),
            QuizOption(
                id="q2_b",
                text="감정과 분위기",
                auteur_weights={"wong": 1.0, "villeneuve": 0.7, "fincher": 0.3},
            ),
            QuizOption(
                id="q2_c",
                text="복잡한 구조와 반전",
                auteur_weights={"nolan": 1.0, "fincher": 0.5, "tarantino": 0.3},
            ),
            QuizOption(
                id="q2_d",
                text="스타일리시한 대화와 액션",
                auteur_weights={"tarantino": 1.0, "wachowski": 0.5, "bong": 0.3},
            ),
        ],
    ),
    QuizQuestion(
        id="q3_emotion",
        dimension=QuizDimension.EMOTION,
        question_ko="당신의 영상이 전달하길 원하는 감정은?",
        question_en="What emotion do you want your video to convey?",
        order=3,
        options=[
            QuizOption(
                id="q3_a",
                text="긴장감과 불안",
                auteur_weights={"fincher": 1.0, "nolan": 0.5, "kubrick": 0.5},
            ),
            QuizOption(
                id="q3_b",
                text="그리움과 멜랑콜리",
                auteur_weights={"wong": 1.0, "villeneuve": 0.5},
            ),
            QuizOption(
                id="q3_c",
                text="경외감과 웅장함",
                auteur_weights={"villeneuve": 1.0, "nolan": 0.7, "kubrick": 0.3},
            ),
            QuizOption(
                id="q3_d",
                text="쿨하고 위트있는",
                auteur_weights={"tarantino": 1.0, "wachowski": 0.5, "bong": 0.3},
            ),
        ],
    ),
    QuizQuestion(
        id="q4_pacing",
        dimension=QuizDimension.PACING,
        question_ko="선호하는 영상 템포는?",
        question_en="What's your preferred video pacing?",
        order=4,
        options=[
            QuizOption(
                id="q4_a",
                text="천천히 쌓아가는 긴장감",
                auteur_weights={"villeneuve": 1.0, "kubrick": 0.7, "fincher": 0.5},
            ),
            QuizOption(
                id="q4_b",
                text="빠른 컷과 강렬한 액션",
                auteur_weights={"tarantino": 1.0, "wachowski": 0.7, "nolan": 0.3},
            ),
            QuizOption(
                id="q4_c",
                text="복잡하게 얽힌 다층 구조",
                auteur_weights={"nolan": 1.0, "tarantino": 0.5, "bong": 0.3},
            ),
            QuizOption(
                id="q4_d",
                text="꿈같이 흐르는 분위기",
                auteur_weights={"wong": 1.0, "villeneuve": 0.5},
            ),
        ],
    ),
    QuizQuestion(
        id="q5_goal",
        dimension=QuizDimension.CREATIVE_GOAL,
        question_ko="당신의 창작 목표는?",
        question_en="What's your creative goal?",
        order=5,
        options=[
            QuizOption(
                id="q5_a",
                text="세상에 메시지를 전달하고 싶다",
                auteur_weights={"bong": 1.0, "wachowski": 0.7, "nolan": 0.3},
            ),
            QuizOption(
                id="q5_b",
                text="아름다운 예술 작품을 만들고 싶다",
                auteur_weights={"wong": 1.0, "villeneuve": 0.7, "kubrick": 0.5},
            ),
            QuizOption(
                id="q5_c",
                text="관객을 놀라게 하고 싶다",
                auteur_weights={"nolan": 1.0, "fincher": 0.7, "tarantino": 0.5},
            ),
            QuizOption(
                id="q5_d",
                text="완벽한 결과물을 만들고 싶다",
                auteur_weights={"kubrick": 1.0, "fincher": 0.7, "villeneuve": 0.3},
            ),
        ],
    ),
]


# ============================================================================
# Style Quiz Service
# ============================================================================

class StyleQuizService:
    """Service for gamified style quiz and auteur DNA matching."""

    def __init__(self):
        """Initialize with quiz questions and auteur profiles."""
        self.questions = QUIZ_QUESTIONS
        self.auteur_profiles = AUTEUR_PROFILES

    def get_questions(self, limit: int = 5) -> List[QuizQuestion]:
        """Get quiz questions.

        Args:
            limit: Maximum number of questions (default 5)

        Returns:
            List of QuizQuestion objects
        """
        sorted_questions = sorted(self.questions, key=lambda q: q.order)
        return sorted_questions[:limit]

    def get_question_by_id(self, question_id: str) -> Optional[QuizQuestion]:
        """Get a specific question by ID."""
        for q in self.questions:
            if q.id == question_id:
                return q
        return None

    def calculate_result(
        self,
        answers: Dict[str, str],  # question_id → option_id
        user_id: Optional[str] = None,
    ) -> QuizResult:
        """Calculate quiz result and auteur DNA matching.

        Args:
            answers: Dict mapping question_id to selected option_id
            user_id: Optional user ID for tracking

        Returns:
            QuizResult with auteur matching
        """
        if not answers:
            return QuizResult(
                success=False,
                primary_match=self._create_default_match(),
                secondary_matches=[],
                dimension_scores={},
                creative_profile={},
                share_text="",
                error="No answers provided",
            )

        # Calculate auteur scores
        auteur_scores: Dict[str, float] = {key: 0.0 for key in AUTEUR_PROFILES.keys()}
        dimension_choices: Dict[str, str] = {}

        for question_id, option_id in answers.items():
            question = self.get_question_by_id(question_id)
            if not question:
                continue

            # Find selected option
            selected_option = None
            for opt in question.options:
                if opt.id == option_id:
                    selected_option = opt
                    break

            if not selected_option:
                continue

            # Add weights to auteur scores
            for auteur_key, weight in selected_option.auteur_weights.items():
                if auteur_key in auteur_scores:
                    auteur_scores[auteur_key] += weight

            # Track dimension choice
            dimension_choices[question.dimension.value] = selected_option.text

        # Sort auteurs by score
        sorted_auteurs = sorted(
            auteur_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Calculate percentages
        total_score = sum(score for _, score in sorted_auteurs if score > 0) or 1
        matches: List[AuteurMatch] = []

        for auteur_key, score in sorted_auteurs:
            if score <= 0:
                continue

            profile = self.auteur_profiles.get(auteur_key, {})
            percentage = round((score / total_score) * 100, 1)

            matches.append(AuteurMatch(
                auteur_key=auteur_key,
                name_ko=profile.get("name_ko", auteur_key),
                name_en=profile.get("name_en", auteur_key),
                match_percentage=percentage,
                signature=profile.get("signature", ""),
                keywords=profile.get("keywords", []),
            ))

        # Primary and secondary matches
        primary = matches[0] if matches else self._create_default_match()
        secondary = matches[1:4] if len(matches) > 1 else []

        # Create creative profile
        creative_profile = self._build_creative_profile(primary, dimension_choices)

        # Generate share text
        share_text = self._generate_share_text(primary)

        # Evidence refs
        evidence_refs = [
            f"rag:quiz:auteur:{primary.auteur_key}",
            "rag:quiz:dna_matching",
        ]

        logger.info(
            f"[STYLE_QUIZ] user={user_id} primary={primary.auteur_key} "
            f"match={primary.match_percentage}%"
        )

        return QuizResult(
            success=True,
            primary_match=primary,
            secondary_matches=secondary,
            dimension_scores=dimension_choices,
            creative_profile=creative_profile,
            share_text=share_text,
            evidence_refs=evidence_refs,
        )

    def _create_default_match(self) -> AuteurMatch:
        """Create default match when no valid answers."""
        return AuteurMatch(
            auteur_key="bong",
            name_ko="봉준호",
            name_en="Bong Joon-ho",
            match_percentage=50.0,
            signature="사회비평 + 장르혼합",
            keywords=["기생충", "괴물"],
        )

    def _build_creative_profile(
        self,
        primary: AuteurMatch,
        dimension_choices: Dict[str, str],
    ) -> Dict[str, Any]:
        """Build creative profile from match result."""
        profile = self.auteur_profiles.get(primary.auteur_key, {})

        return {
            "dominant_style": primary.signature,
            "visual_approach": profile.get("visual_style", [])[:3],
            "narrative_style": profile.get("narrative", [])[:3],
            "emotional_tone": profile.get("emotion", [])[:3],
            "dimension_preferences": dimension_choices,
        }

    def _generate_share_text(self, primary: AuteurMatch) -> str:
        """Generate shareable text for social media."""
        return (
            f"🎬 나의 창작 DNA: {primary.name_ko} 스타일 {primary.match_percentage}% 매칭!\n"
            f"'{primary.signature}'\n"
            f"#CrebitStudio #창작DNA #거장매칭"
        )

    def get_auteur_info(self, auteur_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific auteur."""
        return self.auteur_profiles.get(auteur_key)

    def get_all_auteurs(self) -> List[Dict[str, Any]]:
        """Get list of all available auteurs."""
        return [
            {
                "key": key,
                "name_ko": profile["name_ko"],
                "name_en": profile["name_en"],
                "signature": profile["signature"],
            }
            for key, profile in self.auteur_profiles.items()
        ]


# ============================================================================
# Singleton
# ============================================================================

_style_quiz_service: Optional[StyleQuizService] = None


def get_style_quiz_service() -> StyleQuizService:
    """Get singleton StyleQuizService instance."""
    global _style_quiz_service
    if _style_quiz_service is None:
        _style_quiz_service = StyleQuizService()
    return _style_quiz_service


def _reset_style_quiz_service() -> None:
    """Reset singleton for testing."""
    global _style_quiz_service
    _style_quiz_service = None
