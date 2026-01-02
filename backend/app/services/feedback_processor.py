"""
Feedback Loop Processor

프로덕션 결과 기반 자동 학습 및 신뢰도 갱신 서비스.

Features:
- 실시간 피드백 수집
- 배치 학습 싸이클
- 자동 DNAInvariant 신뢰도 갱신
- 메트릭 기반 증거 생성

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from app.schemas.feedback_schemas import (
    FeedbackEvent, FeedbackType, ProductionResult, UserFeedback,
    LearningCycle, FeedbackProcessorConfig, FeedbackSummary,
    ResultOutcome,
)
from app.schemas.director_pack import DNAInvariant, InvariantType, RuleSpec, RulePriority
from app.schemas.bayesian_schemas import Evidence, ConfidenceUpdate
from app.services.bayesian_engine import BayesianTruthEngine

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """
    피드백 루프 프로세서
    
    Flow:
    1. 피드백 이벤트 수집
    2. 증거로 변환
    3. 베이지안 갱신
    4. 학습 싸이클 완료
    """
    
    def __init__(self, config: Optional[FeedbackProcessorConfig] = None):
        self.config = config or FeedbackProcessorConfig()
        self.bayesian = BayesianTruthEngine()
        
        # 현재 싸이클
        self.current_cycle: Optional[LearningCycle] = None
        
        # 이벤트 버퍼
        self.event_buffer: List[FeedbackEvent] = []
        
        # 규칙 캐시 (실제로는 DB에서 로드)
        self._rules_cache: Dict[str, DNAInvariant] = {}
    
    def start_cycle(self) -> LearningCycle:
        """새 학습 싸이클 시작"""
        self.current_cycle = LearningCycle(
            start_time=datetime.utcnow(),
            status="collecting",
        )
        logger.info(f"Learning cycle started: {self.current_cycle.cycle_id}")
        return self.current_cycle
    
    def process_production_result(
        self,
        result: ProductionResult,
        rules: Optional[List[DNAInvariant]] = None,
    ) -> List[ConfidenceUpdate]:
        """
        프로덕션 결과 처리
        
        Args:
            result: 프로덕션 결과
            rules: 관련 규칙들 (없으면 캐시에서 조회)
        
        Returns:
            신뢰도 갱신 목록
        """
        updates = []
        
        # 1. 관련 규칙 조회
        if rules is None:
            rules = [self._rules_cache.get(r_id) for r_id in result.rule_ids]
            rules = [r for r in rules if r is not None]
        
        if not rules:
            logger.warning(f"No rules found for result: {result.result_id}")
            return updates
        
        # 2. 결과를 증거로 변환
        supports = result.outcome == ResultOutcome.SUCCESS
        strength = self._calculate_evidence_strength(result)
        
        # 3. 각 규칙에 대해 베이지안 갱신
        for rule in rules:
            evidence = Evidence(
                evidence_id=f"prod_{result.result_id}",
                rule_id=rule.rule_id,
                evidence_type="production_result",
                supports_rule=supports,
                strength=strength,
                source_id=result.run_id,
                source_description=f"Production result: {result.outcome.value}",
            )
            
            updated_rule, update = self.bayesian.update_confidence(rule, evidence)
            
            # 캐시 업데이트
            self._rules_cache[rule.rule_id] = updated_rule
            
            updates.append(update)
            
            logger.info(
                f"Rule {rule.rule_id} updated: "
                f"{update.prior:.3f} → {update.posterior:.3f} (delta={update.delta:+.3f})"
            )
        
        # 4. 이벤트 생성 및 버퍼에 추가
        event = FeedbackEvent(
            feedback_type=FeedbackType.PRODUCTION_RESULT,
            production_result=result,
            processed=True,
            processed_at=datetime.utcnow(),
            confidence_updates=[u.model_dump() for u in updates],
        )
        self._add_to_buffer(event)
        
        return updates
    
    def process_user_feedback(
        self,
        feedback: UserFeedback,
        rules: Optional[List[DNAInvariant]] = None,
    ) -> List[ConfidenceUpdate]:
        """
        사용자 피드백 처리
        
        Args:
            feedback: 사용자 피드백
            rules: 관련 규칙들
        
        Returns:
            신뢰도 갱신 목록
        """
        updates = []
        
        if rules is None:
            rules = list(self._rules_cache.values())
        
        if not rules:
            return updates
        
        # 평점 기반 증거 생성
        supports = feedback.rating >= self.config.min_rating_to_support
        strength = (feedback.rating - 1) / 4.0  # 1-5 → 0-1
        
        for rule in rules:
            evidence = Evidence(
                evidence_id=f"user_{feedback.feedback_id}",
                rule_id=rule.rule_id,
                evidence_type="user_feedback",
                supports_rule=supports,
                strength=strength * 0.7,  # 사용자 피드백은 가중치 낮춤
                source_id=feedback.user_id,
                source_description=f"User rating: {feedback.rating}/5",
            )
            
            updated_rule, update = self.bayesian.update_confidence(rule, evidence)
            self._rules_cache[rule.rule_id] = updated_rule
            updates.append(update)
        
        # 이벤트 생성
        event = FeedbackEvent(
            feedback_type=FeedbackType.USER_RATING,
            user_feedback=feedback,
            processed=True,
            processed_at=datetime.utcnow(),
            confidence_updates=[u.model_dump() for u in updates],
        )
        self._add_to_buffer(event)
        
        return updates
    
    def process_metric_update(
        self,
        rule_id: str,
        metric_name: str,
        metric_value: float,
        threshold: float,
    ) -> Optional[ConfidenceUpdate]:
        """
        메트릭 업데이트 처리
        
        예: CTR이 특정 임계값 이상이면 규칙 지지
        """
        rule = self._rules_cache.get(rule_id)
        if not rule:
            return None
        
        supports = metric_value >= threshold
        strength = min(1.0, metric_value / threshold) if threshold > 0 else 0.5
        
        evidence = Evidence(
            evidence_id=f"metric_{uuid4().hex[:8]}",
            rule_id=rule_id,
            evidence_type="metric",
            supports_rule=supports,
            strength=strength,
            source_description=f"{metric_name}: {metric_value:.3f} (threshold: {threshold})",
        )
        
        updated_rule, update = self.bayesian.update_confidence(rule, evidence)
        self._rules_cache[rule_id] = updated_rule
        
        # 이벤트 생성
        event = FeedbackEvent(
            feedback_type=FeedbackType.METRIC_UPDATE,
            raw_data={"rule_id": rule_id, "metric": metric_name, "value": metric_value},
            processed=True,
            processed_at=datetime.utcnow(),
            confidence_updates=[update.model_dump()],
        )
        self._add_to_buffer(event)
        
        return update
    
    def complete_cycle(self) -> Optional[LearningCycle]:
        """
        현재 학습 싸이클 완료
        
        Returns:
            완료된 싸이클
        """
        if not self.current_cycle:
            return None
        
        cycle = self.current_cycle
        cycle.end_time = datetime.utcnow()
        cycle.events = self.event_buffer.copy()
        cycle.event_count = len(self.event_buffer)
        
        # 통계 계산
        total_delta = 0.0
        rules_updated = set()
        
        for event in cycle.events:
            for update in event.confidence_updates:
                total_delta += abs(update.get("delta", 0))
                rules_updated.add(update.get("rule_id"))
        
        cycle.rules_updated = len(rules_updated)
        cycle.total_delta = total_delta
        cycle.avg_confidence_change = total_delta / max(1, cycle.event_count)
        cycle.status = "completed"
        
        logger.info(
            f"Learning cycle completed: {cycle.cycle_id}, "
            f"events={cycle.event_count}, rules_updated={cycle.rules_updated}, "
            f"avg_change={cycle.avg_confidence_change:.4f}"
        )
        
        # 버퍼 초기화
        self.event_buffer = []
        self.current_cycle = None
        
        return cycle
    
    def get_summary(self) -> FeedbackSummary:
        """현재 상태 요약"""
        events = self.event_buffer
        
        events_by_type = defaultdict(int)
        ratings = []
        scores = []
        successes = 0
        total_outcomes = 0
        rules = set()
        
        for event in events:
            events_by_type[event.feedback_type.value] += 1
            
            if event.user_feedback:
                ratings.append(event.user_feedback.rating)
            
            if event.production_result:
                if event.production_result.score:
                    scores.append(event.production_result.score)
                total_outcomes += 1
                if event.production_result.outcome == ResultOutcome.SUCCESS:
                    successes += 1
            
            for update in event.confidence_updates:
                rules.add(update.get("rule_id"))
        
        # 트렌드 계산
        if events:
            recent_deltas = [
                sum(u.get("delta", 0) for u in e.confidence_updates)
                for e in events[-10:]
            ]
            avg_delta = sum(recent_deltas) / len(recent_deltas) if recent_deltas else 0
            trend = "up" if avg_delta > 0.01 else "down" if avg_delta < -0.01 else "stable"
        else:
            trend = "stable"
        
        return FeedbackSummary(
            total_events=len(events),
            events_by_type=dict(events_by_type),
            avg_rating=sum(ratings) / len(ratings) if ratings else None,
            avg_score=sum(scores) / len(scores) if scores else None,
            success_rate=successes / max(1, total_outcomes),
            rules_affected=len(rules),
            confidence_trend=trend,
        )
    
    def register_rule(self, rule: DNAInvariant) -> None:
        """규칙 등록 (캐시)"""
        self._rules_cache[rule.rule_id] = rule
    
    def get_rule(self, rule_id: str) -> Optional[DNAInvariant]:
        """규칙 조회"""
        return self._rules_cache.get(rule_id)
    
    def get_all_rules(self) -> List[DNAInvariant]:
        """모든 규칙 조회"""
        return list(self._rules_cache.values())
    
    def _calculate_evidence_strength(self, result: ProductionResult) -> float:
        """증거 강도 계산"""
        base_strength = 0.5
        
        # 점수 기반 조정
        if result.score is not None:
            if result.score >= 80:
                base_strength = 0.9
            elif result.score >= 60:
                base_strength = 0.7
            elif result.score >= 40:
                base_strength = 0.5
            else:
                base_strength = 0.3
        
        # 메트릭 기반 보정
        if result.metrics:
            engagement = result.metrics.get("engagement_rate", 0)
            if engagement > 0.1:
                base_strength = min(1.0, base_strength + 0.1)
        
        return base_strength
    
    def _add_to_buffer(self, event: FeedbackEvent) -> None:
        """이벤트 버퍼에 추가"""
        self.event_buffer.append(event)
        
        if self.current_cycle:
            self.current_cycle.event_count = len(self.event_buffer)


# 싱글톤 인스턴스
feedback_processor = FeedbackProcessor()
