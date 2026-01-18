"""
Abyss Mirror (심연의 거울) Dimension Endpoints.

사주 + MBTI + 혈액형 → 심층 페르소나 JSON 프리셋 생성
채팅 기반 다중 턴 분석 (최소 15회)

Security:
- XSS sanitization for user_message
- Enum validation for mbti, blood_type, gender, current_stage

2026 Enhancements:
- MBTI Creativity Index (CI) calculation: 3*SN + JP - EI - 0.5*TF
- Creative Style classification (visionary, architect, dramatic, experimental)
- Auteur Affinity matching based on personality type
- Profile Quality assessment for RAG integration
"""
from __future__ import annotations

import html
import logging
import re
import uuid
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List

from app.routers.run_token import verify_run_token  # P3

from ._base import (
    get_db,
    get_current_user,
    get_byok_key,
    _validate_model,
    _strip_string,
    DimensionErrorResponse,
    get_sse_headers,
    Optional,
)

router = APIRouter()

# Module logger
mirror_logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

ALLOWED_BLOOD_TYPES = frozenset({"A", "B", "O", "AB", ""})
ALLOWED_GENDERS = frozenset({"M", "F", "Other", ""})
ALLOWED_STAGES = frozenset({
    "intro", "birth", "saju", "psychology", "creativity",
    "preferences", "synthesis", "final"
})
VALID_MBTI_CHARS = [
    frozenset({"E", "I"}),
    frozenset({"S", "N"}),
    frozenset({"T", "F"}),
    frozenset({"J", "P"}),
]


# ============================================================================
# 2026 Enhancements: MBTI Creativity Index & Creative Styles
# ============================================================================

class CreativeStyle(str, Enum):
    """2026 Creative Style classification based on MBTI-CI research."""
    VISIONARY_STORYTELLER = "visionary_storyteller"
    LOGICAL_ARCHITECT = "logical_architect"
    DRAMATIC_DIRECTOR = "dramatic_director"
    EXPERIMENTAL_ARTIST = "experimental_artist"
    UNKNOWN = "unknown"


# MBTI dimension scores for CI calculation
# E=0, I=1; S=0, N=1; T=0, F=1; J=0, P=1
MBTI_DIMENSION_SCORES = {
    "E": 0, "I": 1,  # EI dimension
    "S": 0, "N": 1,  # SN dimension (highest weight)
    "T": 0, "F": 1,  # TF dimension
    "J": 0, "P": 1,  # JP dimension
}

# Creative style mapping based on MBTI type
MBTI_CREATIVE_STYLE_MAP: Dict[str, CreativeStyle] = {
    # Visionary Storytellers: Feeling-dominant intuitive types
    "INFP": CreativeStyle.VISIONARY_STORYTELLER,
    "ENFP": CreativeStyle.VISIONARY_STORYTELLER,
    "INFJ": CreativeStyle.VISIONARY_STORYTELLER,
    "ENFJ": CreativeStyle.VISIONARY_STORYTELLER,
    # Logical Architects: Thinking-dominant intuitive types
    "INTP": CreativeStyle.LOGICAL_ARCHITECT,
    "INTJ": CreativeStyle.LOGICAL_ARCHITECT,
    "ENTP": CreativeStyle.LOGICAL_ARCHITECT,
    "ENTJ": CreativeStyle.LOGICAL_ARCHITECT,
    # Dramatic Directors: Extroverted judging types
    "ESTJ": CreativeStyle.DRAMATIC_DIRECTOR,
    "ESFJ": CreativeStyle.DRAMATIC_DIRECTOR,
    # Experimental Artists: Perceiving types with sensing
    "ISTP": CreativeStyle.EXPERIMENTAL_ARTIST,
    "ESTP": CreativeStyle.EXPERIMENTAL_ARTIST,
    "ISFP": CreativeStyle.EXPERIMENTAL_ARTIST,
    "ESFP": CreativeStyle.EXPERIMENTAL_ARTIST,
    # Remaining types
    "ISTJ": CreativeStyle.LOGICAL_ARCHITECT,
    "ISFJ": CreativeStyle.VISIONARY_STORYTELLER,
}

# Auteur affinity mapping by creative style
AUTEUR_AFFINITY_MAP: Dict[CreativeStyle, List[str]] = {
    CreativeStyle.VISIONARY_STORYTELLER: ["bong", "wong", "miyazaki", "shinkai"],
    CreativeStyle.LOGICAL_ARCHITECT: ["nolan", "villeneuve", "kubrick", "fincher"],
    CreativeStyle.DRAMATIC_DIRECTOR: ["spielberg", "cameron", "ridley_scott"],
    CreativeStyle.EXPERIMENTAL_ARTIST: ["tarantino", "guy_ritchie", "edgar_wright", "wes_anderson"],
    CreativeStyle.UNKNOWN: [],
}

# Creative strengths by style
CREATIVE_STRENGTHS_MAP: Dict[CreativeStyle, List[str]] = {
    CreativeStyle.VISIONARY_STORYTELLER: [
        "emotional_depth", "character_psychology", "symbolic_expression",
        "atmospheric_storytelling", "visual_metaphor"
    ],
    CreativeStyle.LOGICAL_ARCHITECT: [
        "complex_plot_structure", "worldbuilding", "logical_consistency",
        "conceptual_depth", "precise_execution"
    ],
    CreativeStyle.DRAMATIC_DIRECTOR: [
        "epic_narrative", "character_growth_arc", "emotional_climax",
        "large_scale_storytelling", "audience_engagement"
    ],
    CreativeStyle.EXPERIMENTAL_ARTIST: [
        "genre_blending", "nonlinear_narrative", "technical_innovation",
        "dynamic_pacing", "unconventional_style"
    ],
    CreativeStyle.UNKNOWN: [],
}


def calculate_mbti_creativity_index(mbti: str) -> float:
    """Calculate MBTI Creativity Index using 2026 research formula.

    Formula: CI = 3*SN + JP - EI - 0.5*TF

    Where:
    - SN: 1 if N (intuitive), 0 if S (sensing) - highest weight (3x)
    - JP: 1 if P (perceiving), 0 if J (judging)
    - EI: 1 if I (introvert), 0 if E (extrovert)
    - TF: 1 if F (feeling), 0 if T (thinking)

    Range: -4.5 to +4.5 (higher = more creative potential)

    Args:
        mbti: Validated MBTI type (4 characters, uppercase)

    Returns:
        Creativity Index score (-4.5 to +4.5)
    """
    if not mbti or len(mbti) != 4:
        return 0.0

    # Extract dimension values
    ei = MBTI_DIMENSION_SCORES.get(mbti[0], 0)  # E=0, I=1
    sn = MBTI_DIMENSION_SCORES.get(mbti[1], 0)  # S=0, N=1
    tf = MBTI_DIMENSION_SCORES.get(mbti[2], 0)  # T=0, F=1
    jp = MBTI_DIMENSION_SCORES.get(mbti[3], 0)  # J=0, P=1

    # Apply formula: 3*SN + JP - EI - 0.5*TF
    ci = 3 * sn + jp - ei - 0.5 * tf

    return ci


def get_creative_style(mbti: str) -> CreativeStyle:
    """Determine creative style based on MBTI type.

    Args:
        mbti: Validated MBTI type

    Returns:
        CreativeStyle enum value
    """
    if not mbti or len(mbti) != 4:
        return CreativeStyle.UNKNOWN
    return MBTI_CREATIVE_STYLE_MAP.get(mbti, CreativeStyle.UNKNOWN)


def get_auteur_affinity(creative_style: CreativeStyle) -> List[str]:
    """Get list of auteur keys that match the creative style.

    Args:
        creative_style: CreativeStyle enum value

    Returns:
        List of auteur keys
    """
    return AUTEUR_AFFINITY_MAP.get(creative_style, [])


def get_creative_strengths(creative_style: CreativeStyle) -> List[str]:
    """Get creative strengths for a given style.

    Args:
        creative_style: CreativeStyle enum value

    Returns:
        List of strength keywords
    """
    return CREATIVE_STRENGTHS_MAP.get(creative_style, [])


class MirrorProfileQuality(BaseModel):
    """2026 Profile Quality assessment for Abyss Mirror."""

    # Scores (0-100)
    completeness_score: int = Field(0, ge=0, le=100, description="Data completeness")
    consistency_score: int = Field(0, ge=0, le=100, description="Response consistency")
    depth_score: int = Field(0, ge=0, le=100, description="Analysis depth")
    overall_score: int = Field(0, ge=0, le=100, description="Overall quality")

    # MBTI Creativity Index
    creativity_index: float = Field(0.0, ge=-4.5, le=4.5, description="MBTI-CI score")

    # Creative profile
    creative_style: str = Field("unknown", description="Creative style classification")
    auteur_affinity: List[str] = Field(default_factory=list, description="Matched auteur keys")
    creative_strengths: List[str] = Field(default_factory=list, description="Creative strength areas")

    # Suggestions
    suggestions: List[str] = Field(default_factory=list, description="Improvement tips")


def assess_mirror_profile_quality(
    mbti: str,
    persona_data: Dict[str, Any],
    completion_rate: float,
    chat_turn_count: int = 0,
) -> MirrorProfileQuality:
    """Assess profile quality using 2026 best practices.

    Args:
        mbti: MBTI type (may be empty)
        persona_data: Accumulated persona data
        completion_rate: Current completion percentage
        chat_turn_count: Number of chat turns completed

    Returns:
        MirrorProfileQuality with scores and recommendations
    """
    suggestions: List[str] = []

    # 1. Completeness Score (based on data fields present)
    completeness_factors = []

    # Check MBTI
    if mbti and len(mbti) == 4:
        completeness_factors.append(25)
    else:
        suggestions.append("Provide MBTI type for better creative style matching")

    # Check saju data - verify meaningful content, not just dict presence
    saju_data = persona_data.get("saju", {})
    if isinstance(saju_data, dict) and any(
        v for v in saju_data.values() if isinstance(v, str) and v.strip()
    ):
        completeness_factors.append(25)
    else:
        suggestions.append("Complete saju (四柱) analysis for deeper insights")

    # Check input data - verify at least one meaningful value
    input_data = persona_data.get("input", {})
    if isinstance(input_data, dict) and any(
        v for v in input_data.values() if isinstance(v, str) and v.strip()
    ):
        completeness_factors.append(15)

    # Check persona insights - verify meaningful content
    persona_insights = persona_data.get("persona", {})
    if isinstance(persona_insights, dict) and any(
        v for v in persona_insights.values() if isinstance(v, str) and v.strip()
    ):
        completeness_factors.append(20)

    # Check preferences - verify meaningful content
    preferences = persona_data.get("preferences", {})
    if isinstance(preferences, dict) and any(
        v for v in preferences.values() if v  # Any truthy value
    ):
        completeness_factors.append(15)

    completeness_score = sum(completeness_factors)

    # 2. Consistency Score (based on chat turns)
    if chat_turn_count >= 15:
        consistency_score = 100
    elif chat_turn_count >= 10:
        consistency_score = 80
    elif chat_turn_count >= 5:
        consistency_score = 60
        suggestions.append("Continue the conversation for deeper analysis (aim for 15+ turns)")
    else:
        consistency_score = max(20, chat_turn_count * 10)
        suggestions.append("More conversation needed for reliable personality assessment")

    # 3. Depth Score (based on completion rate)
    depth_score = min(100, int(completion_rate))
    if depth_score < 50:
        suggestions.append("Progress through more analysis stages for comprehensive profile")

    # 4. Calculate MBTI-CI and creative style
    creativity_index = calculate_mbti_creativity_index(mbti)
    creative_style = get_creative_style(mbti)
    auteur_affinity = get_auteur_affinity(creative_style)
    creative_strengths = get_creative_strengths(creative_style)

    # High creativity index suggestion
    if creativity_index >= 3.0:
        suggestions.append("High creative potential detected - explore unconventional narrative structures")
    elif creativity_index <= -1.0:
        suggestions.append("Structured approach recommended - leverage logical worldbuilding strengths")

    # 5. Overall Score
    overall_score = int(
        completeness_score * 0.3 +
        consistency_score * 0.3 +
        depth_score * 0.4
    )

    return MirrorProfileQuality(
        completeness_score=completeness_score,
        consistency_score=consistency_score,
        depth_score=depth_score,
        overall_score=overall_score,
        creativity_index=creativity_index,
        creative_style=creative_style.value,
        auteur_affinity=auteur_affinity,
        creative_strengths=creative_strengths,
        suggestions=suggestions[:5],  # Limit to 5 suggestions
    )


# ============================================================================
# Sanitization Helpers
# ============================================================================

def _sanitize_text_field(value: str, default: str = "") -> str:
    """Sanitize text fields to prevent XSS.

    Args:
        value: Raw text input
        default: Default value if empty

    Returns:
        Sanitized string
    """
    if not value:
        return default
    value = value.strip()
    if not value:
        return default
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value or default


def _validate_mbti(value: str) -> str:
    """Validate MBTI type.

    Args:
        value: Raw MBTI

    Returns:
        Validated MBTI (uppercase) or empty string if invalid
    """
    value = value.upper().strip()
    if not value:
        return ""
    if len(value) != 4:
        return ""
    for i, char in enumerate(value):
        if char not in VALID_MBTI_CHARS[i]:
            return ""
    return value


def _validate_blood_type(value: str) -> str:
    """Validate blood type.

    Args:
        value: Raw blood type

    Returns:
        Validated blood type (uppercase) or empty string if invalid
    """
    value = value.upper().strip()
    if value in ALLOWED_BLOOD_TYPES:
        return value
    return ""


def _validate_gender(value: str) -> str:
    """Validate gender.

    Args:
        value: Raw gender

    Returns:
        Validated gender or empty string if invalid
    """
    value = value.strip()
    # Case-insensitive check
    value_normalized = value.upper() if value else ""
    for g in ALLOWED_GENDERS:
        if g.upper() == value_normalized:
            return g
    return ""


def _validate_stage(value: str) -> str:
    """Validate current stage.

    Args:
        value: Raw stage

    Returns:
        Validated stage

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_STAGES:
        raise ValueError(
            f"지원하지 않는 단계: {value}. Allowed: {sorted(ALLOWED_STAGES)}"
        )
    return value


# ============================================================================
# Request/Response Models
# ============================================================================

class MirrorInitRequest(BaseModel):
    """심연의 거울 초기화 요청.

    Includes:
    - Validation for mbti, blood_type, gender
    """
    mbti: str = Field("", max_length=4, description="MBTI 유형 (예: INTJ)")
    blood_type: str = Field("", max_length=2, description="혈액형 (A/B/O/AB)")
    birth_year: int = Field(..., ge=1900, le=2100, description="출생 연도")
    birth_month: int = Field(..., ge=1, le=12, description="출생 월")
    birth_day: int = Field(..., ge=1, le=31, description="출생 일")
    birth_hour: int = Field(12, ge=0, le=23, description="출생 시간 (0-23)")
    gender: str = Field("", max_length=10, description="성별 (M/F/Other)")
    model: str = Field("gemini-3-flash-preview", description="AI 모델")

    # P5-3: 워크플로우 재진입 필드
    session_id: Optional[str] = Field(None, description="기존 세션 ID (재진입)")
    seed_preset: Optional[Dict[str, Any]] = Field(None, description="시드 프리셋 데이터")
    prior_outputs: Optional[List[Dict[str, Any]]] = Field(None, description="이전 출력 목록")

    @field_validator("mbti", mode="before")
    @classmethod
    def validate_mbti_field(cls, v: str) -> str:
        """Validate MBTI type."""
        return _validate_mbti(v) if v else ""

    @field_validator("blood_type", mode="before")
    @classmethod
    def validate_blood_type_field(cls, v: str) -> str:
        """Validate blood type."""
        return _validate_blood_type(v) if v else ""

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender_field(cls, v: str) -> str:
        """Validate gender."""
        return _validate_gender(v) if v else ""

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class MirrorChatRequest(BaseModel):
    """심연의 거울 채팅 요청.

    Includes:
    - XSS sanitization for user_message
    - Enum validation for current_stage
    """
    session_id: str = Field(..., min_length=1, description="세션 ID")
    user_message: str = Field(..., min_length=1, max_length=2000, description="사용자 메시지 (sanitized)")
    persona_data: Dict[str, Any] = Field(default_factory=dict, description="누적된 페르소나 데이터")
    chat_history: List[Dict[str, str]] = Field(default_factory=list, description="대화 기록")
    current_stage: str = Field("intro", description="현재 분석 단계")
    model: str = Field("gemini-3-flash-preview", description="AI 모델")

    @field_validator("user_message", mode="before")
    @classmethod
    def sanitize_user_message(cls, v: str) -> str:
        """Sanitize user_message to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("current_stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        """Validate current_stage is in allowed list."""
        return _validate_stage(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class MirrorInitResponse(BaseModel):
    """심연의 거울 초기화 응답."""
    success: bool
    session_id: str
    saju: Dict[str, str]
    initial_message: str
    persona_data: Dict[str, Any]
    completion_rate: float
    # 2026 RAG Protocol Fields
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references (format: 'rag:mirror:mbti_profile')",
    )
    # 2026 Profile Quality
    profile_quality: Optional[MirrorProfileQuality] = Field(
        None, description="Profile quality assessment with MBTI-CI"
    )



class MirrorChatResponse(BaseModel):
    """심연의 거울 채팅 응답."""
    success: bool
    ai_response: str
    persona_data: Dict[str, Any]
    completion_rate: float
    current_stage: str
    is_complete: bool
    # RAG Protocol Fields (v2) - P6 evidence_refs as List[str]
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references (format: 'rag:mirror:session_id', 'db:persona:uuid')",
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")
    is_crisis: bool = Field(False, description="Crisis keyword detected - safety response")
    # 2026 Profile Quality
    profile_quality: Optional[MirrorProfileQuality] = Field(
        None, description="Profile quality assessment with MBTI-CI"
    )
    error: Optional[str] = None


class MirrorExportResponse(BaseModel):
    """페르소나 프리셋 내보내기 응답."""
    success: bool
    preset_json: str
    download_filename: str
    # 2026 RAG Protocol Fields
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references",
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/mirror/init",
    response_model=MirrorInitResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        500: {"model": DimensionErrorResponse},
    },
    summary="심연의 거울: 분석 시작",
    description="사주/MBTI/혈액형 입력으로 페르소나 분석 세션 시작",
    tags=["Dimension Extended"],
)
async def init_mirror(
    request: MirrorInitRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> MirrorInitResponse:
    """심연의 거울 분석 세션 초기화."""
    user_id = user.get("id", "unknown")
    mirror_logger.info(
        f"[MIRROR_INIT] user={user_id} mbti={request.mbti} blood={request.blood_type} "
        f"birth={request.birth_year}-{request.birth_month:02d}-{request.birth_day:02d} gender={request.gender}"
    )
    import uuid
    from app.services.mirror_service import (
        calculate_saju_pillars,
        validate_persona_preset,
    )
    
    # 세션 ID 생성 (또는 재사용)
    # P5-3: 기존 세션 ID가 있으면 재사용
    session_id = request.session_id if request.session_id else str(uuid.uuid4())
    
    # 사주 계산
    saju = calculate_saju_pillars(
        year=request.birth_year,
        month=request.birth_month,
        day=request.birth_day,
        hour=request.birth_hour,
    )
    
    # 초기 페르소나 데이터
    persona_data = validate_persona_preset({
        "input": {
            "mbti": request.mbti,
            "blood_type": request.blood_type,
            "birth_datetime": f"{request.birth_year}-{request.birth_month:02d}-{request.birth_day:02d}T{request.birth_hour:02d}:00:00",
            "gender": request.gender,
        },
        "saju": saju,
    })
    
    # P5-3: seed_preset 병합 (화이트리스트 필터링)
    # 우선순위: seed_preset < 사용자 입력 (위에서 계산된 saju 등)
    if request.seed_preset:
        ALLOWED_SEED_FIELDS = {"persona", "saju", "psychology", "creativity", "preferences"}
        filtered_seed = {k: v for k, v in request.seed_preset.items() if k in ALLOWED_SEED_FIELDS}
        # filtered_seed가 기본, persona_data가 덮어쓴다
        persona_data = {**filtered_seed, **persona_data}
    
    # 초기 메시지 생성
    element_names = {
        "목": "나무(木)", "화": "불(火)", "토": "흙(土)", 
        "금": "쇠(金)", "수": "물(水)"
    }
    element_desc = element_names.get(saju.get("dominant_element", ""), "")
    
    mbti_intro = f"MBTI {request.mbti} 유형이시군요! " if request.mbti else ""
    blood_intro = f"혈액형 {request.blood_type}형의 특성과 " if request.blood_type else ""
    
    initial_message = f"""🪞 **심연의 거울에 오신 것을 환영합니다.**

{mbti_intro}{blood_intro}당신의 사주를 분석했습니다.

**사주팔자 분석:**
- 연주: {saju['year_pillar']}
- 월주: {saju['month_pillar']}
- 일주: {saju['day_pillar']} (본인의 핵심)
- 시주: {saju['hour_pillar']}

당신의 일간(日干)은 **{element_desc}** 기운이 강합니다.

이제 당신의 심층 페르소나를 탐구해볼까요? 🔮

**첫 번째 질문:**
어린 시절, 가장 몰입했던 놀이나 활동이 있다면 무엇이었나요? 
(이것은 당신의 핵심 욕구와 창작 성향을 드러냅니다)"""

    # 2026: Generate trace_id and evidence_refs
    trace_id = str(uuid.uuid4())
    evidence_refs: List[str] = []

    # Add MBTI-based evidence if available
    if request.mbti:
        evidence_refs.append(f"rag:mirror:mbti_profile:{request.mbti.lower()}")
        # Creative style evidence
        creative_style = get_creative_style(request.mbti)
        if creative_style != CreativeStyle.UNKNOWN:
            evidence_refs.append(f"rag:mirror:creative_style:{creative_style.value}")

    # Add saju evidence
    if saju.get("dominant_element"):
        evidence_refs.append(f"rag:mirror:saju_element:{saju['dominant_element']}")

    # 2026: Assess profile quality
    profile_quality = assess_mirror_profile_quality(
        mbti=request.mbti,
        persona_data=persona_data,
        completion_rate=25.0,
        chat_turn_count=0,
    )

    mirror_logger.info(
        f"[MIRROR_INIT_2026] trace_id={trace_id} mbti={request.mbti} "
        f"ci={profile_quality.creativity_index:.1f} style={profile_quality.creative_style}"
    )

    return MirrorInitResponse(
        success=True,
        session_id=session_id,
        saju=saju,
        initial_message=initial_message,
        persona_data=persona_data,
        completion_rate=25.0,  # 사주 완료 = 25%
        # 2026 Fields
        trace_id=trace_id,
        evidence_refs=evidence_refs,
        profile_quality=profile_quality,
    )


@router.post(
    "/mirror/chat",
    response_model=MirrorChatResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        401: {"model": DimensionErrorResponse, "description": "Invalid or missing run token"},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="심연의 거울: 채팅 진행",
    description="페르소나 분석 대화 진행 (진행률 업데이트)",
    tags=["Dimension Extended"],
)
async def chat_mirror(
    request: MirrorChatRequest,
    token_data: dict = Depends(verify_run_token),  # P0: Run-Token 강제
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> MirrorChatResponse:
    """심연의 거울 채팅."""
    user_id = user.get("id", "unknown")
    mirror_logger.info(
        f"[MIRROR_CHAT] user={user_id} session={request.session_id} "
        f"stage={request.current_stage} msg_len={len(request.user_message)}"
    )
    from app.services.mirror_service import analyze_persona_with_mirror
    
    # 분석 실행
    result = await analyze_persona_with_mirror(
        user_message=request.user_message,
        persona_data=request.persona_data,
        birth_info={},  # 이미 persona_data에 포함
        current_stage=request.current_stage,
        chat_history=request.chat_history,
        api_key=byok_key,
        model=request.model,
    )

    # P6: LLM-only 모드 - evidence_refs
    trace_id = str(uuid.uuid4())
    evidence_refs: List[str] = [
        f"db:mirror:session:{request.session_id}",
        f"db:mirror:stage:{result['next_stage']}",
    ]

    # 2026: Extract MBTI from persona_data for profile quality
    mbti = ""
    input_data = result.get("updated_persona", {}).get("input", {})
    if isinstance(input_data, dict):
        mbti = input_data.get("mbti", "")

    # Add MBTI-based evidence if available
    if mbti:
        creative_style = get_creative_style(mbti)
        if creative_style != CreativeStyle.UNKNOWN:
            evidence_refs.append(f"rag:mirror:creative_style:{creative_style.value}")

    # 2026: Assess profile quality
    chat_turn_count = len(request.chat_history) // 2 + 1  # Estimate turns
    profile_quality = assess_mirror_profile_quality(
        mbti=mbti,
        persona_data=result["updated_persona"],
        completion_rate=result["completion_rate"],
        chat_turn_count=chat_turn_count,
    )

    mirror_logger.info(
        f"[MIRROR_CHAT_2026] trace_id={trace_id} session={request.session_id} "
        f"stage={result['next_stage']} quality={profile_quality.overall_score}"
    )

    return MirrorChatResponse(
        success="error" not in result,
        ai_response=result["ai_response"],
        persona_data=result["updated_persona"],
        completion_rate=result["completion_rate"],
        current_stage=result["next_stage"],
        is_complete=result["is_complete"],
        # RAG Protocol
        trace_id=trace_id,
        evidence_refs=evidence_refs,
        confidence=min(1.0, profile_quality.overall_score / 100),
        is_crisis=result.get("is_crisis", False),
        # 2026 Profile Quality
        profile_quality=profile_quality,
        error=result.get("error"),
    )


@router.post(
    "/mirror/export",
    response_model=MirrorExportResponse,
    responses={
        400: {"model": DimensionErrorResponse},
    },
    summary="심연의 거울: 프리셋 내보내기",
    description="완성된 페르소나 프리셋을 JSON으로 내보내기",
    tags=["Dimension Extended"],
)
async def export_mirror_preset(
    persona_data: Dict[str, Any],
    user: dict = Depends(get_current_user),
) -> MirrorExportResponse:
    """페르소나 프리셋 내보내기."""
    user_id = user.get("id", "unknown")
    mirror_logger.info(
        f"[MIRROR_EXPORT] user={user_id} persona_keys={list(persona_data.keys())}"
    )
    from app.services.mirror_service import export_persona_preset, validate_persona_preset
    from datetime import datetime
    
    # 유효성 검사 및 기본값 채우기
    validated = validate_persona_preset(persona_data)
    
    # JSON 문자열 생성
    preset_json = export_persona_preset(validated)
    
    # 파일명 생성
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    archetype = validated.get("persona", {}).get("archetype", "persona")
    filename = f"abyss_mirror_{archetype}_{timestamp}.json"
    
    # 2026: Generate trace_id and evidence_refs
    trace_id = str(uuid.uuid4())
    evidence_refs = [f"db:mirror:export:{archetype}"]

    mirror_logger.info(
        f"[MIRROR_EXPORT_2026] trace_id={trace_id} archetype={archetype}"
    )

    return MirrorExportResponse(
        success=True,
        preset_json=preset_json,
        download_filename=filename,
        trace_id=trace_id,
        evidence_refs=evidence_refs,
    )


@router.post(
    "/mirror/chat/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        401: {"model": DimensionErrorResponse, "description": "Unauthorized"},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="심연의 거울: 채팅 진행 (SSE Stream)",
    description="페르소나 분석 대화 진행 (실시간 스트리밍)",
    tags=["Dimension Extended"],
)
async def chat_mirror_stream(
    request: MirrorChatRequest,
    token_data: dict = Depends(verify_run_token),  # P3.5: Run-Token 강제
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """심연의 거울 채팅 스트리밍."""
    user_id = user.get("id", "unknown")
    mirror_logger.info(
        f"[MIRROR_CHAT_STREAM] user={user_id} session={request.session_id} "
        f"stage={request.current_stage} msg_len={len(request.user_message)}"
    )
    import json
    from app.services.run_token_service import get_run_token_service
    
    # P3.5: Run-Token 검증
    if token_data["app_id"] != "ai":
        raise HTTPException(status_code=401, detail="App mismatch")
    
    # P3.5: user_id 매칭 체크
    if token_data["user_id"] != user["user_id"]:
        raise HTTPException(status_code=401, detail="User mismatch")
    
    # P3.5: Run-Token 기반 크레딧 차감
    service = get_run_token_service()
    ok, used, remaining, err = await service.deduct_credits(
        token_data["run_id"], amount=5, reason="mirror_chat_stream"
    )
    if not ok:
        raise HTTPException(status_code=402, detail=err or "Insufficient credits")
    
    async def generate_stream():
        from app.services.mirror_service import analyze_persona_with_mirror

        # 분석 실행
        result = await analyze_persona_with_mirror(
            user_message=request.user_message,
            persona_data=request.persona_data,
            birth_info={},
            current_stage=request.current_stage,
            chat_history=request.chat_history,
            api_key=byok_key,
            model=request.model,
        )

        # 2026: Generate trace_id and evidence_refs
        trace_id = str(uuid.uuid4())
        evidence_refs = [
            f"db:mirror:session:{request.session_id}",
            f"db:mirror:stage:{result.get('next_stage', request.current_stage)}",
        ]

        # 2026: Extract MBTI and calculate profile quality
        mbti = ""
        input_data = result.get("updated_persona", {}).get("input", {})
        if isinstance(input_data, dict):
            mbti = input_data.get("mbti", "")

        if mbti:
            creative_style = get_creative_style(mbti)
            if creative_style != CreativeStyle.UNKNOWN:
                evidence_refs.append(f"rag:mirror:creative_style:{creative_style.value}")

        chat_turn_count = len(request.chat_history) // 2 + 1
        profile_quality = assess_mirror_profile_quality(
            mbti=mbti,
            persona_data=result.get("updated_persona", {}),
            completion_rate=result.get("completion_rate", 0),
            chat_turn_count=chat_turn_count,
        )

        # Add 2026 fields to result
        result["trace_id"] = trace_id
        result["evidence_refs"] = evidence_refs
        result["confidence"] = min(1.0, profile_quality.overall_score / 100)
        result["profile_quality"] = profile_quality.model_dump()

        mirror_logger.info(
            f"[MIRROR_STREAM_2026] trace_id={trace_id} quality={profile_quality.overall_score}"
        )

        # 스트리밍 전송
        yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )

