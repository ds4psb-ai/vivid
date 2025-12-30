"""
Metrics Collection Schema

Defines schemas for collecting and storing real performance metrics:
- Watch time and retention curves
- Engagement metrics (likes, shares, saves, comments)
- Platform-specific data
- A/B test results

Philosophy:
- 측정되지 않으면 최적화할 수 없다
- 실측 데이터가 예측 모델을 보정한다
- Hook 성능은 숫자로 증명해야 한다

License: arkain.info@gmail.com
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class Platform(str, Enum):
    """지원 플랫폼"""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE_LONGFORM = "youtube_longform"
    FACEBOOK = "facebook"
    TWITTER = "twitter"


class MetricType(str, Enum):
    """메트릭 유형"""
    RETENTION = "retention"
    ENGAGEMENT = "engagement"
    REACH = "reach"
    CONVERSION = "conversion"
    AB_TEST = "ab_test"


# =============================================================================
# Retention Metrics
# =============================================================================

class RetentionPoint(BaseModel):
    """단일 잔존율 데이터 포인트"""
    timestamp_sec: float = Field(description="영상 내 시점 (초)")
    retention_rate: float = Field(ge=0.0, le=1.0, description="해당 시점 잔존율")
    sample_size: int = Field(default=0, description="해당 시점까지 본 사람 수")


class RetentionCurve(BaseModel):
    """잔존율 곡선"""
    data_points: List[RetentionPoint] = Field(default_factory=list)
    
    # 핵심 지표
    retention_1_5s: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    retention_3s: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    retention_10s: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    retention_30s: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    retention_60s: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # 평균/완료
    avg_watch_time_sec: Optional[float] = Field(default=None)
    avg_percentage_watched: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    completion_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # 드롭오프 분석
    biggest_drop_timestamp: Optional[float] = Field(default=None, description="가장 큰 이탈 발생 시점")
    biggest_drop_rate: Optional[float] = Field(default=None, description="해당 시점 이탈률")


# =============================================================================
# Engagement Metrics
# =============================================================================

class EngagementMetrics(BaseModel):
    """참여도 메트릭"""
    
    # 카운트
    views: int = Field(default=0)
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    shares: int = Field(default=0)
    saves: int = Field(default=0, description="저장/북마크 수")
    
    # 비율 (views 기준)
    like_rate: Optional[float] = Field(default=None, ge=0.0)
    comment_rate: Optional[float] = Field(default=None, ge=0.0)
    share_rate: Optional[float] = Field(default=None, ge=0.0)
    save_rate: Optional[float] = Field(default=None, ge=0.0)
    
    # 종합 점수
    engagement_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # 바이럴 지표
    virality_score: Optional[float] = Field(
        default=None, 
        description="(shares + saves) / views"
    )
    
    def calculate_rates(self):
        """비율 계산"""
        if self.views > 0:
            self.like_rate = self.likes / self.views
            self.comment_rate = self.comments / self.views
            self.share_rate = self.shares / self.views
            self.save_rate = self.saves / self.views
            self.virality_score = (self.shares + self.saves) / self.views
            
            # 종합 점수 (가중 평균)
            self.engagement_score = min(1.0, (
                self.like_rate * 0.2 +
                self.comment_rate * 0.3 +
                self.share_rate * 0.3 +
                self.save_rate * 0.2
            ) * 10)


# =============================================================================
# Reach Metrics
# =============================================================================

class ReachMetrics(BaseModel):
    """도달 메트릭"""
    impressions: int = Field(default=0, description="노출 수")
    reach: int = Field(default=0, description="도달 (고유 사용자)")
    
    # 팔로워 관련
    followers_at_post: int = Field(default=0, description="게시 당시 팔로워")
    new_followers: int = Field(default=0, description="이 콘텐츠로 인한 신규 팔로워")
    
    # 소스
    reach_from_home: Optional[float] = Field(default=None, description="홈/피드에서 온 비율")
    reach_from_explore: Optional[float] = Field(default=None, description="탐색/추천에서 온 비율")
    reach_from_hashtags: Optional[float] = Field(default=None, description="해시태그에서 온 비율")
    reach_from_shares: Optional[float] = Field(default=None, description="공유에서 온 비율")


# =============================================================================
# Content Metrics (종합)
# =============================================================================

class ContentMetrics(BaseModel):
    """콘텐츠 종합 메트릭"""
    
    # 식별
    content_id: str = Field(description="콘텐츠 ID")
    platform: Platform = Field(description="플랫폼")
    platform_content_id: Optional[str] = Field(default=None, description="플랫폼 내 ID")
    
    # 메타정보
    posted_at: datetime = Field(description="게시 시각")
    duration_sec: float = Field(description="영상 길이")
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 세부 메트릭
    retention: RetentionCurve = Field(default_factory=RetentionCurve)
    engagement: EngagementMetrics = Field(default_factory=EngagementMetrics)
    reach: ReachMetrics = Field(default_factory=ReachMetrics)
    
    # Hook 관련 (Phase 4 연동)
    hook_variant_id: Optional[str] = Field(default=None, description="사용된 훅 변형 ID")
    hook_style: Optional[str] = Field(default=None)
    
    # Director Pack 관련
    director_pack_id: Optional[str] = Field(default=None)
    
    # 태그
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


# =============================================================================
# A/B Test Results
# =============================================================================

class ABTestVariantResult(BaseModel):
    """A/B 테스트 단일 변형 결과"""
    variant_id: str
    variant_style: str
    
    # 샘플
    sample_size: int = Field(default=0)
    
    # 핵심 지표
    retention_1_5s: float = Field(ge=0.0, le=1.0)
    retention_10s: float = Field(ge=0.0, le=1.0)
    engagement_score: float = Field(ge=0.0, le=1.0)
    
    # 승자 여부
    is_winner: bool = Field(default=False)
    improvement_vs_control: Optional[float] = Field(
        default=None,
        description="대조군 대비 개선율 (%)"
    )


class ABTestResult(BaseModel):
    """A/B 테스트 결과"""
    
    test_id: str = Field(description="테스트 ID")
    test_name: str
    
    # 기간
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    # 변형별 결과
    variant_results: List[ABTestVariantResult] = Field(default_factory=list)
    
    # 승자
    winning_variant_id: Optional[str] = None
    winning_style: Optional[str] = None
    statistical_significance: Optional[float] = Field(
        default=None,
        description="통계적 유의성 (0-1, 0.95+ 권장)"
    )
    
    # 인사이트
    key_insights: List[str] = Field(default_factory=list)
    
    # 다음 액션
    recommended_action: Optional[str] = None


# =============================================================================
# Metrics Collection Request/Response
# =============================================================================

class MetricsSubmission(BaseModel):
    """메트릭 제출 요청"""
    content_id: str
    platform: Platform
    platform_content_id: Optional[str] = None
    
    # 기본 정보
    posted_at: datetime
    duration_sec: float
    
    # 메트릭 (선택적)
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    saves: Optional[int] = None
    
    # 잔존율 (선택적)
    avg_watch_time_sec: Optional[float] = None
    avg_percentage_watched: Optional[float] = None
    retention_data: Optional[List[Dict]] = None
    
    # 도달 (선택적)
    impressions: Optional[int] = None
    reach: Optional[int] = None
    
    # Hook 정보
    hook_variant_id: Optional[str] = None
    hook_style: Optional[str] = None
    director_pack_id: Optional[str] = None
    
    # 추가 데이터
    extra_data: Optional[Dict[str, Any]] = None


class MetricsResponse(BaseModel):
    """메트릭 제출 응답"""
    success: bool
    metrics_id: str
    content_id: str
    
    # 분석 결과
    performance_grade: str = Field(description="A/B/C/D/F 등급")
    compared_to_benchmark: str = Field(description="벤치마크 대비 평가")
    
    # 개선 제안
    suggestions: List[str] = Field(default_factory=list)


# =============================================================================
# Aggregated Metrics
# =============================================================================

class MetricsAggregate(BaseModel):
    """집계된 메트릭 (기간별/스타일별)"""
    
    # 집계 기준
    group_by: str = Field(description="집계 기준 (date, hook_style, platform 등)")
    group_value: str
    
    # 기간
    period_start: datetime
    period_end: datetime
    
    # 샘플
    content_count: int
    total_views: int
    
    # 평균 지표
    avg_retention_1_5s: float
    avg_retention_10s: float
    avg_engagement_score: float
    avg_virality_score: float
    
    # 최고/최저
    best_content_id: Optional[str] = None
    best_engagement: Optional[float] = None
    worst_content_id: Optional[str] = None
    worst_engagement: Optional[float] = None


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_performance_grade(
    retention_1_5s: float,
    engagement_score: float,
    platform: Platform = Platform.INSTAGRAM,
) -> str:
    """성과 등급 계산"""
    # 플랫폼별 기준 (간단한 버전)
    score = retention_1_5s * 0.5 + engagement_score * 0.5
    
    if score >= 0.8:
        return "A"
    elif score >= 0.6:
        return "B"
    elif score >= 0.4:
        return "C"
    elif score >= 0.2:
        return "D"
    else:
        return "F"


def compare_to_benchmark(
    metrics: ContentMetrics,
    benchmark_retention: float = 0.65,
    benchmark_engagement: float = 0.03,
) -> str:
    """벤치마크 대비 평가"""
    retention = metrics.retention.retention_1_5s or 0
    engagement = metrics.engagement.engagement_score or 0
    
    retention_diff = (retention - benchmark_retention) / benchmark_retention * 100
    engagement_diff = (engagement - benchmark_engagement) / benchmark_engagement * 100
    
    if retention_diff > 20 and engagement_diff > 20:
        return f"🚀 벤치마크 대비 매우 우수 (잔존율 +{retention_diff:.0f}%, 참여도 +{engagement_diff:.0f}%)"
    elif retention_diff > 0 and engagement_diff > 0:
        return f"✅ 벤치마크 초과 (잔존율 +{retention_diff:.0f}%, 참여도 +{engagement_diff:.0f}%)"
    elif retention_diff > 0 or engagement_diff > 0:
        return f"⚠️ 부분적 초과"
    else:
        return f"📉 벤치마크 미달 (개선 필요)"
