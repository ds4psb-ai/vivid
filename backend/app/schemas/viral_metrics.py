"""
Viral Metrics Schema

Defines metrics for predicting and measuring viral potential:
- Hook Retention: 1.5s/3s/10s retention prediction
- Dissonance: familiar + unexpected tension scoring
- Engagement: share/save/comment prediction

Philosophy:
- DNA = 품질 (Quality)
- Narrative = 의미 (Meaning)  
- Viral = 전파력 (Spreadability)

License: arkain.info@gmail.com
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class ViralPotential(str, Enum):
    """바이럴 잠재력 수준"""
    LOW = "low"           # 평범
    MODERATE = "moderate" # 보통
    HIGH = "high"         # 높음
    VIRAL = "viral"       # 폭발적


class RiskLevel(str, Enum):
    """부조화 리스크 수준"""
    SAFE = "safe"         # 안전 (무난)
    MODERATE = "moderate" # 보통 (약간의 긴장)
    BOLD = "bold"         # 대담 (강한 부조화)
    RISKY = "risky"       # 위험 (너무 강함, 역효과 가능)


class DissonanceType(str, Enum):
    """부조화 유형"""
    CLASS_CONTRAST = "class_contrast"       # 계급 대비 (봉준호 스타일)
    SITUATION_PARADOX = "situation_paradox" # 상황 역설
    CHARACTER_CONTRADICTION = "character_contradiction"  # 캐릭터 모순
    VISUAL_CONTRAST = "visual_contrast"     # 시각적 대비
    TONE_SHIFT = "tone_shift"               # 톤 전환
    EXPECTATION_SUBVERSION = "expectation_subversion"  # 기대 전복


# =============================================================================
# Hook Retention
# =============================================================================

class HookRetentionScore(BaseModel):
    """훅 잔존율 예측"""
    
    # 시점별 예상 잔존율 (0-1)
    t_1_5s: float = Field(
        ge=0.0, le=1.0,
        description="1.5초 시점 예상 잔존율"
    )
    t_3s: float = Field(
        ge=0.0, le=1.0,
        description="3초 시점 예상 잔존율"
    )
    t_10s: float = Field(
        ge=0.0, le=1.0,
        description="10초 시점 예상 잔존율"
    )
    t_30s: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="30초 시점 예상 잔존율 (중장편용)"
    )
    
    # 예상 이탈 원인
    drop_off_reason: Optional[str] = Field(
        default=None,
        description="주요 이탈 예상 원인 (예: '훅 약함', '템포 느림')"
    )
    
    # 훅 강도 분석
    hook_strength: Literal["weak", "moderate", "strong", "explosive"] = Field(
        default="moderate",
        description="훅 강도 평가"
    )
    
    # 개선 제안
    improvement_tips: List[str] = Field(
        default_factory=list,
        description="잔존율 개선 제안"
    )


# =============================================================================
# Dissonance Score
# =============================================================================

class DissonanceScore(BaseModel):
    """익숙함 + 낯섦 부조화 점수"""
    
    # 부조화 요소
    familiar_element: str = Field(
        description="익숙한 요소 (예: 'NBA 스타', '일상적 아침')"
    )
    unexpected_element: str = Field(
        description="예상치 못한 요소 (예: '치킨집 사장', '갑자기 좀비')"
    )
    
    # 부조화 유형
    dissonance_type: DissonanceType = Field(
        description="부조화 유형"
    )
    
    # 점수
    tension_level: float = Field(
        ge=0.0, le=1.0,
        description="긴장도 (0: 무난, 1: 극적)"
    )
    curiosity_level: float = Field(
        ge=0.0, le=1.0,
        description="호기심 유발도"
    )
    
    # 리스크
    risk_level: RiskLevel = Field(
        default=RiskLevel.MODERATE,
        description="부조화 리스크 수준"
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="잠재적 리스크 요소"
    )
    
    # 효과 예측
    predicted_effect: str = Field(
        default="호기심 유발",
        description="예상 효과 (호기심, 충격, 웃음, 불편함 등)"
    )


# =============================================================================
# Engagement Prediction
# =============================================================================

class EngagementPrediction(BaseModel):
    """참여도 예측"""
    
    # 확률 예측 (0-1)
    share_probability: float = Field(
        ge=0.0, le=1.0,
        description="공유 확률"
    )
    save_probability: float = Field(
        ge=0.0, le=1.0,
        description="저장 확률"
    )
    comment_probability: float = Field(
        ge=0.0, le=1.0,
        description="댓글 확률"
    )
    like_probability: float = Field(
        ge=0.0, le=1.0,
        description="좋아요 확률"
    )
    
    # 종합 점수
    engagement_score: float = Field(
        ge=0.0, le=1.0,
        description="종합 참여도 점수"
    )
    
    # 바이럴 잠재력
    viral_potential: ViralPotential = Field(
        default=ViralPotential.MODERATE,
        description="바이럴 잠재력 수준"
    )
    
    # 예상 코멘트 유형
    likely_comment_themes: List[str] = Field(
        default_factory=list,
        description="예상 댓글 주제 (예: '웃음', '공감', '논란')"
    )
    
    # 타겟 오디언스
    best_fit_audience: List[str] = Field(
        default_factory=list,
        description="가장 적합한 타겟층 (예: 'MZ세대', '영화 팬')"
    )


# =============================================================================
# Complete Viral Analysis Report
# =============================================================================

class ViralAnalysisReport(BaseModel):
    """전체 바이럴 분석 리포트"""
    
    # 메타
    content_id: str = Field(description="콘텐츠 ID")
    platform: str = Field(
        default="instagram",
        description="타겟 플랫폼"
    )
    analyzed_at: Optional[str] = Field(default=None)
    
    # 핵심 지표
    hook_retention: HookRetentionScore
    dissonance: Optional[DissonanceScore] = Field(default=None)
    engagement: EngagementPrediction
    
    # 종합 평가
    overall_viral_score: float = Field(
        ge=0.0, le=1.0,
        description="종합 바이럴 점수"
    )
    overall_potential: ViralPotential = Field(
        description="종합 바이럴 잠재력"
    )
    
    # 강점/약점
    strengths: List[str] = Field(
        default_factory=list,
        description="바이럴 강점"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="바이럴 약점"
    )
    
    # 추천 액션
    recommendations: List[str] = Field(
        default_factory=list,
        description="개선 추천 사항"
    )
    
    # A/B 테스트 제안
    ab_test_suggestions: List[str] = Field(
        default_factory=list,
        description="A/B 테스트 제안 (훅 변형 등)"
    )


# =============================================================================
# Platform-specific Benchmarks
# =============================================================================

class PlatformBenchmarks(BaseModel):
    """플랫폼별 기준치"""
    
    platform: str
    
    # 잔존율 기준
    avg_retention_1_5s: float = 0.7
    avg_retention_10s: float = 0.4
    
    # 참여도 기준
    avg_share_rate: float = 0.02
    avg_save_rate: float = 0.05
    
    # 바이럴 임계점
    viral_threshold_shares: int = 1000
    viral_threshold_saves: int = 500


# 플랫폼별 기본 벤치마크
PLATFORM_BENCHMARKS = {
    "instagram": PlatformBenchmarks(
        platform="instagram",
        avg_retention_1_5s=0.65,
        avg_retention_10s=0.35,
        avg_share_rate=0.015,
        avg_save_rate=0.04,
    ),
    "tiktok": PlatformBenchmarks(
        platform="tiktok",
        avg_retention_1_5s=0.60,
        avg_retention_10s=0.30,
        avg_share_rate=0.025,
        avg_save_rate=0.06,
    ),
    "youtube_shorts": PlatformBenchmarks(
        platform="youtube_shorts",
        avg_retention_1_5s=0.70,
        avg_retention_10s=0.40,
        avg_share_rate=0.01,
        avg_save_rate=0.03,
    ),
    "youtube_longform": PlatformBenchmarks(
        platform="youtube_longform",
        avg_retention_1_5s=0.80,
        avg_retention_10s=0.60,
        avg_share_rate=0.008,
        avg_save_rate=0.02,
    ),
}


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_viral_potential(
    retention_1_5s: float,
    engagement_score: float,
    dissonance_tension: float = 0.5,
) -> ViralPotential:
    """바이럴 잠재력 계산"""
    
    # 가중 점수 계산
    score = (
        retention_1_5s * 0.4 +
        engagement_score * 0.4 +
        dissonance_tension * 0.2
    )
    
    if score >= 0.8:
        return ViralPotential.VIRAL
    elif score >= 0.6:
        return ViralPotential.HIGH
    elif score >= 0.4:
        return ViralPotential.MODERATE
    else:
        return ViralPotential.LOW


def get_platform_benchmark(platform: str) -> PlatformBenchmarks:
    """플랫폼 벤치마크 가져오기"""
    return PLATFORM_BENCHMARKS.get(
        platform, 
        PLATFORM_BENCHMARKS["instagram"]
    )
