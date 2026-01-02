"""
Unit Tests for Feedback Processor

Coverage Target: 80%+
"""
import pytest
from app.services.feedback_processor import FeedbackProcessor, feedback_processor
from app.schemas.feedback_schemas import (
    ProductionResult, UserFeedback, ResultOutcome,
    FeedbackEvent, FeedbackType, LearningCycle,
)
from app.schemas.director_pack import DNAInvariant, InvariantType, RuleSpec


class TestFeedbackProcessor:
    """피드백 프로세서 테스트"""
    
    @pytest.fixture
    def processor(self):
        proc = FeedbackProcessor()
        # 테스트용 규칙 등록
        rule = DNAInvariant(
            rule_id="test_rule_1",
            rule_type=InvariantType.ENGAGEMENT,
            name="Test Rule",
            condition="engagement_rate",
            spec=RuleSpec(operator="gt", value=0.5),
            confidence=0.5,
        )
        proc.register_rule(rule)
        return proc
    
    @pytest.fixture
    def sample_result(self):
        return ProductionResult(
            capsule_id="cap_123",
            run_id="run_123",
            outcome=ResultOutcome.SUCCESS,
            score=85.0,
            rule_ids=["test_rule_1"],
            metrics={"engagement_rate": 0.08},
        )
    
    @pytest.fixture
    def sample_feedback(self):
        return UserFeedback(
            capsule_id="cap_123",
            user_id="user_123",
            rating=5,
            comment="Great video!",
        )
    
    # 규칙 등록 테스트
    def test_register_rule(self, processor):
        """규칙 등록"""
        rule = DNAInvariant(
            rule_id="new_rule",
            rule_type=InvariantType.TIMING,
            name="New Rule",
            condition="hook_time",
            spec=RuleSpec(operator="lt", value=2.0),
        )
        processor.register_rule(rule)
        
        assert processor.get_rule("new_rule") is not None
    
    def test_get_all_rules(self, processor):
        """모든 규칙 조회"""
        rules = processor.get_all_rules()
        assert len(rules) >= 1
    
    # 프로덕션 결과 처리 테스트
    def test_process_production_result_success(self, processor, sample_result):
        """성공 결과 처리"""
        updates = processor.process_production_result(sample_result)
        
        assert len(updates) == 1
        assert updates[0].posterior > updates[0].prior
        assert updates[0].delta > 0
    
    def test_process_production_result_failure(self, processor):
        """실패 결과 처리"""
        result = ProductionResult(
            outcome=ResultOutcome.FAILURE,
            score=20.0,
            rule_ids=["test_rule_1"],
        )
        updates = processor.process_production_result(result)
        
        assert len(updates) == 1
        assert updates[0].posterior < updates[0].prior
        assert updates[0].delta < 0
    
    def test_process_production_result_no_rules(self, processor):
        """규칙 없는 결과"""
        result = ProductionResult(
            outcome=ResultOutcome.SUCCESS,
            rule_ids=["nonexistent_rule"],
        )
        updates = processor.process_production_result(result)
        
        assert len(updates) == 0
    
    # 사용자 피드백 처리 테스트
    def test_process_user_feedback_positive(self, processor, sample_feedback):
        """긍정 피드백 처리"""
        updates = processor.process_user_feedback(sample_feedback)
        
        assert len(updates) >= 1
    
    def test_process_user_feedback_negative(self, processor):
        """부정 피드백 처리"""
        feedback = UserFeedback(
            rating=1,
            comment="Bad",
        )
        updates = processor.process_user_feedback(feedback)
        
        # 낮은 평점은 규칙을 반박 (또는 변화 없음)
        for update in updates:
            assert update.delta <= 0
    
    # 메트릭 업데이트 테스트
    def test_process_metric_update_above_threshold(self, processor):
        """임계값 이상 메트릭"""
        update = processor.process_metric_update(
            rule_id="test_rule_1",
            metric_name="ctr",
            metric_value=0.08,
            threshold=0.05,
        )
        
        assert update is not None
        assert update.delta > 0
    
    def test_process_metric_update_below_threshold(self, processor):
        """임계값 이하 메트릭"""
        update = processor.process_metric_update(
            rule_id="test_rule_1",
            metric_name="ctr",
            metric_value=0.02,
            threshold=0.05,
        )
        
        assert update is not None
        assert update.delta < 0
    
    def test_process_metric_update_unknown_rule(self, processor):
        """존재하지 않는 규칙"""
        update = processor.process_metric_update(
            rule_id="unknown",
            metric_name="ctr",
            metric_value=0.1,
            threshold=0.05,
        )
        
        assert update is None
    
    # 학습 싸이클 테스트
    def test_start_cycle(self, processor):
        """싸이클 시작"""
        cycle = processor.start_cycle()
        
        assert cycle is not None
        assert cycle.status == "collecting"
        assert processor.current_cycle is not None
    
    def test_complete_cycle(self, processor, sample_result):
        """싸이클 완료"""
        processor.start_cycle()
        processor.process_production_result(sample_result)
        
        cycle = processor.complete_cycle()
        
        assert cycle is not None
        assert cycle.status == "completed"
        assert cycle.event_count >= 1
        assert processor.current_cycle is None
    
    def test_complete_cycle_no_active(self, processor):
        """활성 싸이클 없이 완료"""
        cycle = processor.complete_cycle()
        assert cycle is None
    
    # 요약 테스트
    def test_get_summary(self, processor, sample_result, sample_feedback):
        """요약 조회"""
        processor.process_production_result(sample_result)
        processor.process_user_feedback(sample_feedback)
        
        summary = processor.get_summary()
        
        assert summary.total_events == 2
        assert summary.success_rate == 1.0
        assert summary.rules_affected >= 1
    
    def test_get_summary_empty(self, processor):
        """빈 상태 요약"""
        summary = processor.get_summary()
        
        assert summary.total_events == 0
        assert summary.confidence_trend == "stable"


class TestEvidenceStrength:
    """증거 강도 계산 테스트"""
    
    @pytest.fixture
    def processor(self):
        return FeedbackProcessor()
    
    def test_high_score_strength(self, processor):
        """높은 점수 → 높은 강도"""
        result = ProductionResult(score=90.0, outcome=ResultOutcome.SUCCESS)
        strength = processor._calculate_evidence_strength(result)
        assert strength >= 0.8
    
    def test_low_score_strength(self, processor):
        """낮은 점수 → 낮은 강도"""
        result = ProductionResult(score=30.0, outcome=ResultOutcome.FAILURE)
        strength = processor._calculate_evidence_strength(result)
        assert strength <= 0.4
    
    def test_engagement_boost(self, processor):
        """높은 참여도 → 강도 증가"""
        result = ProductionResult(
            score=70.0,
            outcome=ResultOutcome.SUCCESS,
            metrics={"engagement_rate": 0.15},
        )
        strength = processor._calculate_evidence_strength(result)
        assert strength >= 0.7


class TestFeedbackIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스"""
        assert feedback_processor is not None
        assert isinstance(feedback_processor, FeedbackProcessor)
    
    def test_full_feedback_cycle(self):
        """전체 피드백 싸이클"""
        proc = FeedbackProcessor()
        
        # 1. 규칙 등록
        rule = DNAInvariant(
            rule_id="integration_test",
            rule_type=InvariantType.TIMING,
            name="Integration Test Rule",
            condition="test",
            spec=RuleSpec(operator="gt", value=0),
            confidence=0.5,
        )
        proc.register_rule(rule)
        
        # 2. 싸이클 시작
        cycle = proc.start_cycle()
        assert cycle.status == "collecting"
        
        # 3. 프로덕션 결과 처리
        result = ProductionResult(
            outcome=ResultOutcome.SUCCESS,
            score=80.0,
            rule_ids=["integration_test"],
        )
        updates = proc.process_production_result(result)
        assert len(updates) == 1
        
        # 4. 사용자 피드백 처리
        feedback = UserFeedback(rating=4)
        proc.process_user_feedback(feedback)
        
        # 5. 싸이클 완료
        completed = proc.complete_cycle()
        assert completed.event_count == 2
        assert completed.rules_updated >= 1
        
        # 6. 규칙 신뢰도 확인
        updated_rule = proc.get_rule("integration_test")
        assert updated_rule.confidence > 0.5
        assert updated_rule.evidence_count >= 1
