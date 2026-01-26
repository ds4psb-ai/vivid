"""
Intent Inference Helpers for Dimension API Routes.

프론트엔드 요청 파라미터(mood, style, reference_style 등)를
CreativeIntent로 변환하여 Resolver 시스템과 연결합니다.

Usage:
    from app.routers.intent_helpers import infer_intent_from_request
    
    intent = infer_intent_from_request(
        mood=request.mood,
        style=request.style,
        reference_style=request.reference_style,
    )
"""
from __future__ import annotations

from typing import Optional, List
import logging

from app.schemas.creative_intent import (
    CreativeIntent,
    CreativeMood,
    CreativePace,
    TargetAudience,
    ContentDomain,
)

logger = logging.getLogger(__name__)


# =========================================================================
# Mood String → Enum Mapping
# Actual values: CINEMATIC, ENERGETIC, CALM, DOCUMENTARY, EXPERIMENTAL, NOSTALGIC, DARK, WHIMSICAL
# =========================================================================

MOOD_MAPPING = {
    # Direct matches
    "calm": CreativeMood.CALM,
    "energetic": CreativeMood.ENERGETIC,
    "dark": CreativeMood.DARK,
    "cinematic": CreativeMood.CINEMATIC,
    "documentary": CreativeMood.DOCUMENTARY,
    "experimental": CreativeMood.EXPERIMENTAL,
    "nostalgic": CreativeMood.NOSTALGIC,
    "whimsical": CreativeMood.WHIMSICAL,
    
    # Korean/English aliases
    "neutral": CreativeMood.CALM,
    "dramatic": CreativeMood.DARK,
    "mysterious": CreativeMood.DARK,
    "romantic": CreativeMood.NOSTALGIC,
    "dreamy": CreativeMood.NOSTALGIC,
    "epic": CreativeMood.CINEMATIC,
    "tense": CreativeMood.DARK,
    "horror": CreativeMood.DARK,
    "happy": CreativeMood.WHIMSICAL,
    "playful": CreativeMood.WHIMSICAL,
    "sad": CreativeMood.NOSTALGIC,
    "melancholic": CreativeMood.NOSTALGIC,
    "action": CreativeMood.ENERGETIC,
    "intense": CreativeMood.ENERGETIC,
}


# =========================================================================
# Style → Domain Mapping
# =========================================================================

REFERENCE_STYLE_TO_DOMAIN = {
    # AI Auteur Personas (한국 이름)
    "kang": ContentDomain.AUTEUR_BONG,  # 강주노 - 양면의 시선
    "yoon": ContentDomain.AUTEUR_BONG,  # 윤수하 - 어둠의 미학
    "seoyeon": ContentDomain.AUTEUR_BONG,  # 민서연 - 폭풍의 긴장

    # AI Auteur Personas (글로벌)
    "velvet": ContentDomain.AUTEUR_WONG,  # 렌 벨벳 - 네온 속 감정
    "epoch": ContentDomain.AUTEUR_NOLAN,  # 테오 에포크 - 시간의 설계자
    "voltage": ContentDomain.AUTEUR_TARANTINO,  # 렉스 볼티지 - 폭발적 에너지
    "abyss": ContentDomain.AUTEUR_VILLENEUVE,  # 오리온 어비스 - 우주의 심연
    "azure": ContentDomain.AUTEUR_VILLENEUVE,  # 소라 아주르 - 하늘빛 서정
    "prism": ContentDomain.AUTEUR_NOLAN,  # 마일로 프리즘 - 기하학적 완벽

    # Style-based
    "cinematic": ContentDomain.GENRE_DRAMA,
    "documentary": ContentDomain.GENRE_DOCUMENTARY,
    "anime": ContentDomain.GENRE_SCIFI,
    "artistic": ContentDomain.GENRE_DRAMA,
}


# =========================================================================
# Genre → Domain Mapping
# =========================================================================

GENRE_TO_DOMAIN = {
    "drama": ContentDomain.GENRE_DRAMA,
    "thriller": ContentDomain.GENRE_THRILLER,
    "horror": ContentDomain.GENRE_HORROR,
    "comedy": ContentDomain.GENRE_COMEDY,
    "documentary": ContentDomain.GENRE_DOCUMENTARY,
    "scifi": ContentDomain.GENRE_SCIFI,
    "ad": ContentDomain.GENRE_DRAMA,
    "mv": ContentDomain.GENRE_DRAMA,
    "short": ContentDomain.GENRE_DRAMA,
    "romance": ContentDomain.GENRE_DRAMA,
}


# =========================================================================
# Tempo → Pace Mapping
# Actual values: FAST, SLOW, DYNAMIC, CONTEMPLATIVE
# =========================================================================

TEMPO_TO_PACE = {
    "slow": CreativePace.SLOW,
    "medium": CreativePace.DYNAMIC,  # No MEDIUM, map to DYNAMIC
    "fast": CreativePace.FAST,
    "dynamic": CreativePace.DYNAMIC,
    "variable": CreativePace.DYNAMIC,
    "contemplative": CreativePace.CONTEMPLATIVE,
}


# =========================================================================
# Main Inference Function
# =========================================================================

def infer_intent_from_request(
    mood: Optional[str] = None,
    style: Optional[str] = None,
    reference_style: Optional[str] = None,
    genre: Optional[str] = None,
    tempo: Optional[str] = None,
    target_medium: Optional[str] = None,
    sound_type: Optional[str] = None,
) -> Optional[CreativeIntent]:
    """
    프론트엔드 요청 파라미터에서 CreativeIntent 추론.
    
    Args:
        mood: 분위기 (예: "cinematic", "dramatic", "calm")
        style: 스타일 (예: "cinematic", "documentary")
        reference_style: AI 거장 스타일 (예: "kang", "velvet", "epoch")
        genre: 장르 (예: "drama", "thriller", "horror")
        tempo: 템포 (예: "slow", "medium", "fast")
        target_medium: 타겟 미디어 (예: "video", "image")
        sound_type: 사운드 타입 (예: "bgm", "sfx")
        
    Returns:
        CreativeIntent or None if no parameters provided
    """
    # Skip if no relevant parameters
    if not any([mood, style, reference_style, genre, tempo]):
        return None
    
    # 1. Mood 변환
    creative_mood = CreativeMood.CALM  # default
    for key in [mood, style]:
        if key:
            mapped = MOOD_MAPPING.get(key.lower().strip())
            if mapped:
                creative_mood = mapped
                break
    
    # 2. Domain sources 추론
    domain_sources: List[ContentDomain] = []
    
    # Reference style → Auteur domain
    if reference_style:
        domain = REFERENCE_STYLE_TO_DOMAIN.get(reference_style.lower().strip())
        if domain and domain not in domain_sources:
            domain_sources.append(domain)
    
    # Style → Domain (if not already from reference)
    if style:
        domain = REFERENCE_STYLE_TO_DOMAIN.get(style.lower().strip())
        if domain and domain not in domain_sources:
            domain_sources.append(domain)
    
    # Genre → Domain
    if genre:
        domain = GENRE_TO_DOMAIN.get(genre.lower().strip())
        if domain and domain not in domain_sources:
            domain_sources.append(domain)
    
    # 3. Pace 추론
    pace = CreativePace.DYNAMIC  # default
    if tempo:
        pace = TEMPO_TO_PACE.get(tempo.lower().strip(), CreativePace.DYNAMIC)
    elif creative_mood == CreativeMood.ENERGETIC:
        pace = CreativePace.FAST
    elif creative_mood == CreativeMood.CALM:
        pace = CreativePace.SLOW
    
    # 4. Keywords 수집
    keywords: List[str] = []
    if style and style.lower() not in MOOD_MAPPING:
        keywords.append(style.lower())
    if reference_style:
        keywords.append(reference_style.lower())
    
    # 5. Target audience 추론 (optional)
    target = TargetAudience.GENERAL
    if target_medium == "image":
        target = TargetAudience.VISUAL_ARTIST
    
    intent = CreativeIntent(
        mood=creative_mood,
        pace=pace,
        target=target,
        domain_sources=domain_sources,
        keywords=keywords[:5],  # max 5
    )
    
    logger.debug(f"Inferred intent: mood={creative_mood.value}, pace={pace.value}, domains={len(domain_sources)}")
    
    return intent


# =========================================================================
# Specialized Inference for Different Endpoints
# =========================================================================

def infer_intent_for_aesthetic(
    concept: str,
    mood: Optional[str] = None,
    reference_style: Optional[str] = None,
    target_medium: Optional[str] = None,
) -> Optional[CreativeIntent]:
    """Aesthetic Director 전용 Intent 추론."""
    intent = infer_intent_from_request(
        mood=mood,
        reference_style=reference_style,
        target_medium=target_medium,
    )
    
    # Aesthetic은 기본적으로 cinematic mood 선호
    if intent is None:
        intent = CreativeIntent(mood=CreativeMood.CINEMATIC)
    
    return intent


def infer_intent_for_sound(
    concept: str,
    mood: Optional[str] = None,
    genre: Optional[str] = None,
    tempo: Optional[str] = None,
    sound_type: Optional[str] = None,
) -> Optional[CreativeIntent]:
    """Sound Crafter 전용 Intent 추론."""
    intent = infer_intent_from_request(
        mood=mood,
        genre=genre,
        tempo=tempo,
        sound_type=sound_type,
    )
    
    # Sound는 tempo가 중요
    if intent and tempo:
        intent.pace = TEMPO_TO_PACE.get(tempo.lower().strip(), CreativePace.DYNAMIC)
    
    return intent


def infer_intent_for_story(
    concept: str,
    genre: Optional[str] = None,
    structure: Optional[str] = None,
) -> Optional[CreativeIntent]:
    """Story Architect 전용 Intent 추론."""
    intent = infer_intent_from_request(genre=genre)
    
    # Genre가 없으면 drama 기본값
    if intent is None and genre:
        domain = GENRE_TO_DOMAIN.get(genre.lower().strip(), ContentDomain.GENRE_DRAMA)
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            domain_sources=[domain],
        )
    
    return intent


# =========================================================================
# Exports
# =========================================================================

__all__ = [
    "infer_intent_from_request",
    "infer_intent_for_aesthetic",
    "infer_intent_for_sound",
    "infer_intent_for_story",
    "MOOD_MAPPING",
    "REFERENCE_STYLE_TO_DOMAIN",
    "GENRE_TO_DOMAIN",
    "TEMPO_TO_PACE",
    # FastAPI Depends
    "get_intent_dependency",
    "IntentParams",
]


# =========================================================================
# FastAPI Depends-based Intent Injection
# =========================================================================

from dataclasses import dataclass
from typing import Callable
from functools import wraps


@dataclass
class IntentParams:
    """Intent 추론에 사용되는 파라미터 그룹."""
    mood: Optional[str] = None
    style: Optional[str] = None
    reference_style: Optional[str] = None
    genre: Optional[str] = None
    tempo: Optional[str] = None
    target_medium: Optional[str] = None
    sound_type: Optional[str] = None
    concept: Optional[str] = None
    structure: Optional[str] = None


def get_intent_dependency(
    intent_type: str = "general"
) -> Callable:
    """
    FastAPI Depends용 Intent 팩토리.
    
    Usage:
        @router.post("/endpoint")
        async def my_endpoint(
            request: MyRequest,
            intent: Optional[CreativeIntent] = Depends(get_intent_dependency("aesthetic")),
        ):
            return await _execute_dimension_tool(..., intent=intent)
    
    Args:
        intent_type: "general", "aesthetic", "sound", "story" 중 하나
    
    Returns:
        FastAPI Depends에서 사용 가능한 함수
    """
    
    def _extract_intent_from_body():
        """Request body에서 Intent 추론 (Body에서 직접 추출하는 것은 불가)."""
        # Note: FastAPI에서 Body는 한 번만 읽을 수 있어서
        # endpoint 내에서 직접 호출하는 것이 더 안전함
        return None
    
    return _extract_intent_from_body


def create_intent_extractor(
    intent_type: str = "general",
    mood_field: str = "mood",
    style_field: str = "style",
    reference_style_field: str = "reference_style",
    genre_field: str = "genre",
    tempo_field: str = "tempo",
    concept_field: str = "concept",
    structure_field: str = "structure",
):
    """
    Request 객체에서 Intent를 추출하는 함수를 생성.
    
    Usage:
        extract = create_intent_extractor("aesthetic", mood_field="mood", reference_style_field="reference_style")
        intent = extract(request)
    """
    def extractor(request) -> Optional[CreativeIntent]:
        # Extract fields from request
        mood = getattr(request, mood_field, None)
        style = getattr(request, style_field, None)
        reference_style = getattr(request, reference_style_field, None)
        genre = getattr(request, genre_field, None)
        tempo = getattr(request, tempo_field, None)
        concept = getattr(request, concept_field, None)
        structure = getattr(request, structure_field, None)
        
        if intent_type == "aesthetic":
            return infer_intent_for_aesthetic(
                concept=concept or "",
                mood=mood,
                reference_style=reference_style,
                target_medium=getattr(request, "target_medium", None),
            )
        elif intent_type == "sound":
            return infer_intent_for_sound(
                concept=concept or "",
                mood=mood,
                genre=genre,
                tempo=tempo,
                sound_type=getattr(request, "sound_type", None),
            )
        elif intent_type == "story":
            return infer_intent_for_story(
                concept=concept or "",
                genre=genre,
                structure=structure,
            )
        else:
            return infer_intent_from_request(
                mood=mood,
                style=style,
                reference_style=reference_style,
                genre=genre,
                tempo=tempo,
            )
    
    return extractor


# Pre-built extractors for common use cases
aesthetic_intent = create_intent_extractor("aesthetic")
sound_intent = create_intent_extractor("sound")
story_intent = create_intent_extractor("story")
general_intent = create_intent_extractor("general")


def with_intent(request, intent_type: str = "general") -> Optional[CreativeIntent]:
    """
    간편한 Intent 추출 함수.
    
    Usage:
        intent = with_intent(request, "aesthetic")
        # 또는
        intent = with_intent(request)  # general
    """
    if intent_type == "aesthetic":
        return aesthetic_intent(request)
    elif intent_type == "sound":
        return sound_intent(request)
    elif intent_type == "story":
        return story_intent(request)
    else:
        return general_intent(request)


# Update exports
__all__.extend([
    "create_intent_extractor",
    "aesthetic_intent",
    "sound_intent", 
    "story_intent",
    "general_intent",
    "with_intent",
])
