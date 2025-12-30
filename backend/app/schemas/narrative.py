"""
Narrative Structure Schema

Defines the story arc and narrative roles for shots and sequences.
Enables Story-First validation alongside DNA style checking.

Philosophy:
- NarrativeArc = What (story structure)  
- DirectorPack DNA = How (visual style)
- Together they ensure both meaning and aesthetics

License: arkain.info@gmail.com
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class NarrativePhase(str, Enum):
    """서사 단계 (Narrative Phase)"""
    HOOK = "hook"           # 시선 잡기 (0-1.5초, 시퀀스 시작마다)
    SETUP = "setup"         # 상황 설정
    BUILD = "build"         # 긴장 고조
    TURN = "turn"           # 전환점/반전
    PAYOFF = "payoff"       # 보상/해소
    CLIMAX = "climax"       # 클라이맥스
    RESOLUTION = "resolution"  # 해결
    TRANSITION = "transition"  # 전환 (시퀀스 간)


class ArcType(str, Enum):
    """서사 구조 유형"""
    THREE_ACT = "3-act"           # 고전 3막 구조
    FIVE_ACT = "5-act"            # 5막 구조
    HOOK_PAYOFF = "hook-payoff"   # 숏폼 훅-페이오프
    MYSTERY = "mystery"           # 미스터리/서스펜스
    BUILDUP = "buildup"           # 점진적 고조
    EPISODIC = "episodic"         # 에피소드형 (독립 시퀀스들)


class HookContext(str, Enum):
    """훅이 적용되는 컨텍스트"""
    SHORTFORM_START = "shortform_start"     # 숏폼 영상 시작
    SEQUENCE_START = "sequence_start"       # 시퀀스 시작 (장편의 각 시퀀스마다)
    COLD_OPEN = "cold_open"                 # 콜드 오픈
    ACT_TRANSITION = "act_transition"       # 막 전환
    POST_BREAK = "post_break"               # 광고/쉬는 시간 후
    EPISODE_START = "episode_start"         # 에피소드 시작


# =============================================================================
# Shot Narrative Role
# =============================================================================

class ShotNarrativeRole(BaseModel):
    """단일 샷의 서사적 역할"""
    
    shot_id: str = Field(description="샷 ID")
    phase: NarrativePhase = Field(description="이 샷의 서사 단계")
    
    # Hook 관련
    hook_required: bool = Field(
        default=False,
        description="이 샷에 Hook이 필요한가? (시퀀스 시작, 숏폼 시작 등)"
    )
    hook_context: Optional[HookContext] = Field(
        default=None,
        description="Hook 컨텍스트 (hook_required=True일 때)"
    )
    
    # 기대감 흐름
    expectation_created: Optional[str] = Field(
        default=None,
        description="이 샷이 만드는 기대감/의문 (예: '왜 그가 여기 있지?')"
    )
    expectation_fulfilled: Optional[str] = Field(
        default=None,
        description="이 샷이 충족하는 기대감 (이전 샷에서 만든 것)"
    )
    
    # 부조화 요소 (익숙함 + 낯섦)
    dissonance_element: Optional[str] = Field(
        default=None,
        description="이 샷의 부조화 요소 (예: 'NBA 선수가 치킨 튀기는 중')"
    )
    
    # 감정
    target_emotion: Optional[str] = Field(
        default=None,
        description="목표 감정 (호기심, 긴장, 놀람, 감동 등)"
    )
    
    # 시퀀스 정보
    sequence_id: Optional[str] = Field(
        default=None,
        description="소속 시퀀스 ID (장편 구조에서)"
    )
    is_sequence_start: bool = Field(
        default=False,
        description="시퀀스의 첫 샷인가?"
    )


# =============================================================================
# Sequence (for longform)
# =============================================================================

class Sequence(BaseModel):
    """시퀀스 (장편의 구조 단위)"""
    
    sequence_id: str = Field(description="시퀀스 ID")
    name: str = Field(description="시퀀스 이름 (예: '오프닝', '대결', '엔딩')")
    
    # 시간 범위
    t_start: float = Field(description="시작 시간 (초)")
    t_end: float = Field(description="종료 시간 (초)")
    
    # 서사 위치
    act: int = Field(default=1, description="소속 막 (1, 2, 3...)")
    phase: NarrativePhase = Field(description="이 시퀀스의 주요 서사 역할")
    
    # Hook 설정
    hook_recommended: bool = Field(
        default=True,
        description="이 시퀀스 시작에 Hook 추천?"
    )
    hook_intensity: Literal["soft", "medium", "strong"] = Field(
        default="medium",
        description="Hook 강도 추천"
    )
    
    # 포함 샷 ID
    shot_ids: List[str] = Field(default_factory=list)


# =============================================================================
# Narrative Arc
# =============================================================================

class NarrativeArc(BaseModel):
    """전체 콘텐츠의 서사 구조"""
    
    arc_id: str = Field(description="Arc ID")
    arc_type: ArcType = Field(description="서사 구조 유형")
    
    # 기본 정보
    title: Optional[str] = Field(default=None, description="콘텐츠 제목/피치")
    duration_sec: float = Field(description="전체 길이 (초)")
    is_longform: bool = Field(
        default=False,
        description="장편 여부 (True면 시퀀스 구조 사용)"
    )
    
    # 시퀀스 (장편용)
    sequences: List[Sequence] = Field(
        default_factory=list,
        description="장편의 시퀀스들"
    )
    
    # 샷별 역할 (전체)
    shot_roles: List[ShotNarrativeRole] = Field(
        default_factory=list,
        description="각 샷의 서사 역할"
    )
    
    # 감정 곡선
    emotion_start: str = Field(
        default="neutral",
        description="시작 감정 (호기심, 불안, 기대 등)"
    )
    emotion_peak: str = Field(
        default="excited",
        description="클라이맥스 감정"
    )
    emotion_end: str = Field(
        default="satisfied",
        description="마무리 감정"
    )
    
    # 부조화 설계 (바이럴 핵심)
    dissonance_type: Optional[str] = Field(
        default=None,
        description="부조화 유형 (계급대비, 상황역설, 캐릭터모순)"
    )
    familiar_element: Optional[str] = Field(
        default=None,
        description="익숙한 요소 (예: 'NBA 스타')"
    )
    unexpected_element: Optional[str] = Field(
        default=None,
        description="낯선/예상치 못한 요소 (예: '치킨집 사장')"
    )
    
    # 메타
    created_at: Optional[str] = Field(default=None)
    version: str = Field(default="1.0.0")


# =============================================================================
# Arc Compliance Report
# =============================================================================

class ArcRuleResult(BaseModel):
    """서사 규칙 검증 결과"""
    rule_id: str
    rule_name: str
    level: Literal["compliant", "partial", "violation", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    message: str
    affected_shots: List[str] = Field(default_factory=list)


class ArcComplianceReport(BaseModel):
    """서사 구조 준수 리포트"""
    
    arc_id: str
    arc_type: ArcType
    
    # 전체 결과
    overall_level: Literal["compliant", "partial", "violation", "unknown"]
    overall_confidence: float = Field(ge=0.0, le=1.0)
    
    # 상세 결과
    rule_results: List[ArcRuleResult] = Field(default_factory=list)
    
    # Hook 분석
    hook_coverage: float = Field(
        description="시퀀스 시작 중 Hook이 있는 비율 (0-1)"
    )
    missing_hooks: List[str] = Field(
        default_factory=list,
        description="Hook이 없는 시퀀스 시작점들"
    )
    
    # 기대감 분석
    expectation_fulfillment_rate: float = Field(
        default=0.0,
        description="생성된 기대감 중 충족된 비율"
    )
    unfulfilled_expectations: List[str] = Field(
        default_factory=list,
        description="충족되지 않은 기대감들"
    )
    
    # 제안
    suggestions: List[str] = Field(default_factory=list)


# =============================================================================
# Helper Functions
# =============================================================================

def get_recommended_hook_contexts(is_longform: bool, sequences: List[Sequence] = None) -> List[dict]:
    """
    Hook이 필요한 컨텍스트 추천
    
    - 숏폼: 시작 1개
    - 장편: 각 시퀀스 시작마다 (선택적 스위칭 가능)
    """
    if not is_longform:
        return [{
            "context": HookContext.SHORTFORM_START,
            "required": True,
            "timing": "1.5s",
            "intensity": "strong",
        }]
    
    # 장편: 각 시퀀스마다
    result = []
    for seq in (sequences or []):
        result.append({
            "context": HookContext.SEQUENCE_START,
            "sequence_id": seq.sequence_id,
            "sequence_name": seq.name,
            "required": seq.hook_recommended,  # 스위칭 가능
            "timing": "1.5s",
            "intensity": seq.hook_intensity,
            "t_start": seq.t_start,
        })
    
    return result
