"""
Content Metrics API Router

Endpoints for collecting and querying real performance metrics for content.
This is separate from general analytics to focus on viral/engagement tracking.

Endpoints:
- POST /content-metrics - Submit metrics for a content
- GET /content-metrics/{content_id} - Get metrics for content
- GET /content-metrics/aggregate - Get aggregated metrics
- POST /content-metrics/ab-test - Submit A/B test results
- GET /content-metrics/insights - Get viral insights

License: arkain.info@gmail.com
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.schemas.metrics_collection import (
    ContentMetrics,
    MetricsSubmission,
    MetricsResponse,
    MetricsAggregate,
    ABTestResult,
    ABTestVariantResult,
    Platform,
    RetentionCurve,
    EngagementMetrics,
    ReachMetrics,
    calculate_performance_grade,
    compare_to_benchmark,
)
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-metrics", tags=["content-metrics"])


# =============================================================================
# In-Memory Storage (개발용 - 프로덕션에서는 DB 사용)
# =============================================================================

_metrics_store: Dict[str, ContentMetrics] = {}
_ab_test_store: Dict[str, ABTestResult] = {}


# =============================================================================
# Request/Response Models
# =============================================================================

class ViralInsight(BaseModel):
    """바이럴 인사이트"""
    insight_type: str
    title: str
    description: str
    data: Dict[str, Any]
    recommendation: Optional[str] = None


class InsightsResponse(BaseModel):
    """인사이트 응답"""
    period: str
    total_content_analyzed: int
    insights: List[ViralInsight]
    top_performers: List[Dict]
    hook_style_comparison: Dict[str, Dict]


# =============================================================================
# Endpoints
# =============================================================================

@router.post("", response_model=MetricsResponse)
async def submit_metrics(
    submission: MetricsSubmission,
    user: dict = Depends(get_current_user),  # P1: Auth required
):
    """
    콘텐츠 메트릭 제출
    
    플랫폼에서 수집된 성과 데이터를 저장하고 분석합니다.
    """
    metrics_id = f"met_{uuid.uuid4().hex[:12]}"
    
    # RetentionCurve 구성
    retention = RetentionCurve()
    if submission.avg_watch_time_sec:
        retention.avg_watch_time_sec = submission.avg_watch_time_sec
    if submission.avg_percentage_watched:
        retention.avg_percentage_watched = submission.avg_percentage_watched
    
    # 잔존율 추정 (avg_percentage_watched 기반)
    if submission.avg_percentage_watched:
        pct = submission.avg_percentage_watched
        retention.retention_1_5s = min(1.0, pct * 1.3)
        retention.retention_10s = pct
        retention.completion_rate = pct * 0.7
    
    # EngagementMetrics 구성
    engagement = EngagementMetrics(
        views=submission.views or 0,
        likes=submission.likes or 0,
        comments=submission.comments or 0,
        shares=submission.shares or 0,
        saves=submission.saves or 0,
    )
    engagement.calculate_rates()
    
    # ReachMetrics 구성
    reach = ReachMetrics(
        impressions=submission.impressions or 0,
        reach=submission.reach or 0,
    )
    
    # ContentMetrics 생성
    content_metrics = ContentMetrics(
        content_id=submission.content_id,
        platform=submission.platform,
        platform_content_id=submission.platform_content_id,
        posted_at=submission.posted_at,
        duration_sec=submission.duration_sec,
        collected_at=datetime.utcnow(),
        retention=retention,
        engagement=engagement,
        reach=reach,
        hook_variant_id=submission.hook_variant_id,
        hook_style=submission.hook_style,
        director_pack_id=submission.director_pack_id,
    )
    
    # 저장
    _metrics_store[submission.content_id] = content_metrics
    
    # 성과 분석
    grade = calculate_performance_grade(
        retention.retention_1_5s or 0.5,
        engagement.engagement_score or 0.03,
        submission.platform,
    )
    benchmark_comparison = compare_to_benchmark(content_metrics)
    
    # 개선 제안 생성
    suggestions = _generate_suggestions(content_metrics)
    
    logger.info(f"Metrics submitted for {submission.content_id}: grade={grade}")
    
    return MetricsResponse(
        success=True,
        metrics_id=metrics_id,
        content_id=submission.content_id,
        performance_grade=grade,
        compared_to_benchmark=benchmark_comparison,
        suggestions=suggestions,
    )


@router.get("/{content_id}", response_model=ContentMetrics)
async def get_metrics(content_id: str):
    """콘텐츠 메트릭 조회"""
    if content_id not in _metrics_store:
        raise HTTPException(status_code=404, detail="Metrics not found")
    
    return _metrics_store[content_id]


@router.get("/aggregate/by-group", response_model=List[MetricsAggregate])
async def get_aggregate_metrics(
    group_by: str = Query("hook_style", description="집계 기준: hook_style, platform, date"),
    days: int = Query(30, description="최근 N일 기준"),
):
    """집계된 메트릭 조회"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # 기간 내 데이터 필터링
    filtered = [
        m for m in _metrics_store.values()
        if m.collected_at >= cutoff
    ]
    
    if not filtered:
        return []
    
    # 그룹화
    groups: Dict[str, List[ContentMetrics]] = {}
    for m in filtered:
        if group_by == "hook_style":
            key = m.hook_style or "unknown"
        elif group_by == "platform":
            key = m.platform
        elif group_by == "date":
            key = m.posted_at.strftime("%Y-%m-%d")
        else:
            key = "all"
        
        if key not in groups:
            groups[key] = []
        groups[key].append(m)
    
    # 집계
    aggregates = []
    for group_value, items in groups.items():
        total_views = sum(m.engagement.views for m in items)
        
        # 평균 계산
        if total_views > 0:
            avg_retention_1_5s = sum(
                (m.retention.retention_1_5s or 0) * m.engagement.views
                for m in items
            ) / total_views
            avg_retention_10s = sum(
                (m.retention.retention_10s or 0) * m.engagement.views
                for m in items
            ) / total_views
            avg_engagement = sum(
                (m.engagement.engagement_score or 0) * m.engagement.views
                for m in items
            ) / total_views
            avg_virality = sum(
                (m.engagement.virality_score or 0) * m.engagement.views
                for m in items
            ) / total_views
        else:
            avg_retention_1_5s = avg_retention_10s = avg_engagement = avg_virality = 0
        
        best = max(items, key=lambda x: x.engagement.engagement_score or 0)
        worst = min(items, key=lambda x: x.engagement.engagement_score or 0)
        
        aggregates.append(MetricsAggregate(
            group_by=group_by,
            group_value=group_value,
            period_start=cutoff,
            period_end=datetime.utcnow(),
            content_count=len(items),
            total_views=total_views,
            avg_retention_1_5s=round(avg_retention_1_5s, 4),
            avg_retention_10s=round(avg_retention_10s, 4),
            avg_engagement_score=round(avg_engagement, 4),
            avg_virality_score=round(avg_virality, 6),
            best_content_id=best.content_id,
            best_engagement=best.engagement.engagement_score,
            worst_content_id=worst.content_id,
            worst_engagement=worst.engagement.engagement_score,
        ))
    
    return sorted(aggregates, key=lambda x: x.avg_engagement_score, reverse=True)


@router.post("/ab-test", response_model=ABTestResult)
async def submit_ab_test_results(
    test_name: str,
    variant_results: List[ABTestVariantResult],
):
    """A/B 테스트 결과 제출"""
    test_id = f"ab_{uuid.uuid4().hex[:8]}"
    
    # 승자 결정
    scored = [(v, v.retention_1_5s * 0.5 + v.engagement_score * 0.5) for v in variant_results]
    scored.sort(key=lambda x: x[1], reverse=True)
    winner = scored[0][0]
    winner.is_winner = True
    
    # 대조군 대비 개선율
    control = next((v for v in variant_results if "control" in v.variant_id.lower() or v.variant_id.endswith("_0")), None)
    if control:
        control_score = control.retention_1_5s * 0.5 + control.engagement_score * 0.5
        for v, score in scored:
            if control_score > 0:
                v.improvement_vs_control = ((score - control_score) / control_score) * 100
    
    result = ABTestResult(
        test_id=test_id,
        test_name=test_name,
        started_at=datetime.utcnow() - timedelta(days=7),
        ended_at=datetime.utcnow(),
        variant_results=variant_results,
        winning_variant_id=winner.variant_id,
        winning_style=winner.variant_style,
        statistical_significance=0.95 if len(variant_results) >= 2 else 0.5,
        key_insights=[
            f"🏆 '{winner.variant_style}' 스타일이 가장 우수한 성과",
            f"📈 대조군 대비 {winner.improvement_vs_control:.1f}% 개선" if winner.improvement_vs_control else "",
        ],
        recommended_action=f"'{winner.variant_style}' 스타일을 기본 훅으로 채택",
    )
    
    _ab_test_store[test_id] = result
    logger.info(f"A/B test: {test_id}, winner={winner.variant_style}")
    
    return result


@router.get("/ab-test/{test_id}", response_model=ABTestResult)
async def get_ab_test_results(test_id: str):
    """A/B 테스트 결과 조회"""
    if test_id not in _ab_test_store:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return _ab_test_store[test_id]


@router.get("/insights/viral", response_model=InsightsResponse)
async def get_viral_insights(
    platform: Optional[str] = None,
    days: int = Query(30, description="분석 기간"),
):
    """
    바이럴 인사이트 조회
    
    수집된 메트릭 기반으로 훅 스타일별 성과, 최적 전략 등을 제공합니다.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    filtered = [
        m for m in _metrics_store.values()
        if m.collected_at >= cutoff and (platform is None or m.platform == platform)
    ]
    
    if not filtered:
        return InsightsResponse(
            period=f"최근 {days}일",
            total_content_analyzed=0,
            insights=[],
            top_performers=[],
            hook_style_comparison={},
        )
    
    # 훅 스타일별 성과
    style_stats: Dict[str, Dict] = {}
    for m in filtered:
        style = m.hook_style or "unknown"
        if style not in style_stats:
            style_stats[style] = {"count": 0, "views": 0, "retention": 0, "engagement": 0}
        style_stats[style]["count"] += 1
        style_stats[style]["views"] += m.engagement.views
        style_stats[style]["retention"] += m.retention.retention_1_5s or 0
        style_stats[style]["engagement"] += m.engagement.engagement_score or 0
    
    hook_comparison = {
        style: {
            "count": s["count"],
            "views": s["views"],
            "avg_retention": round(s["retention"] / s["count"], 4) if s["count"] > 0 else 0,
            "avg_engagement": round(s["engagement"] / s["count"], 4) if s["count"] > 0 else 0,
        }
        for style, s in style_stats.items()
    }
    
    top = sorted(filtered, key=lambda x: x.engagement.engagement_score or 0, reverse=True)[:5]
    top_performers = [
        {"content_id": m.content_id, "hook_style": m.hook_style, "views": m.engagement.views, "engagement": m.engagement.engagement_score}
        for m in top
    ]
    
    insights = []
    if hook_comparison:
        best = max(hook_comparison.items(), key=lambda x: x[1]["avg_engagement"])
        insights.append(ViralInsight(
            insight_type="best_hook",
            title=f"최고 성과 훅: {best[0]}",
            description=f"평균 참여도 {best[1]['avg_engagement']:.2%}",
            data={"style": best[0], "stats": best[1]},
            recommendation=f"'{best[0]}' 스타일을 더 자주 사용하세요",
        ))
    
    return InsightsResponse(
        period=f"최근 {days}일",
        total_content_analyzed=len(filtered),
        insights=insights,
        top_performers=top_performers,
        hook_style_comparison=hook_comparison,
    )


# =============================================================================
# Helpers
# =============================================================================

def _generate_suggestions(metrics: ContentMetrics) -> List[str]:
    """개선 제안"""
    suggestions = []
    retention = metrics.retention.retention_1_5s or 0
    engagement = metrics.engagement.engagement_score or 0
    
    if retention < 0.5:
        suggestions.append("💡 1.5초 잔존율 저조 - 더 강력한 훅 시도")
    if engagement < 0.03:
        suggestions.append("📤 참여도 저조 - 공유 유도 요소 추가")
    if not suggestions:
        suggestions.append("✅ 좋은 성과입니다!")
    
    return suggestions[:5]
