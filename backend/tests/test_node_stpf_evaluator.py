"""
Unit Tests for Node STPF Evaluator

Coverage Target: 80%+
"""
import pytest
from app.services.node_stpf_evaluator import (
    NodeSTPFEvaluator, node_stpf_evaluator,
    NodeEvaluation, GradeAction, AlternativeSuggestion,
    GRADE_UNICORN, GRADE_HIGH_POTENTIAL, GRADE_RED_OCEAN,
    INTENT_TYPE_RISK, PROPERTY_RISK,
)
from app.schemas.intent_schemas import NodeEditIntent, IntentType


class TestGradeConstants:
    """Grade 상수 테스트"""
    
    def test_grade_order(self):
        """Grade 순서"""
        assert GRADE_UNICORN > GRADE_HIGH_POTENTIAL > GRADE_RED_OCEAN > 0
    
    def test_intent_type_risk(self):
        """의도 유형별 리스크"""
        assert INTENT_TYPE_RISK[IntentType.DELETE] > INTENT_TYPE_RISK[IntentType.MODIFY]
        assert INTENT_TYPE_RISK[IntentType.PREVIEW] == 0
    
    def test_property_risk(self):
        """속성별 리스크"""
        assert PROPERTY_RISK["mood"] >= PROPERTY_RISK["name"]
        assert PROPERTY_RISK["lighting"] >= PROPERTY_RISK["description"]


class TestNodeSTPFEvaluator:
    """Node STPF Evaluator 테스트"""
    
    @pytest.fixture
    def evaluator(self):
        return NodeSTPFEvaluator()
    
    @pytest.fixture
    def simple_intent(self):
        return NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="밝게",
            simple_changes={"lighting": 8},
            overall_confidence=0.9,
        )
    
    @pytest.fixture
    def risky_intent(self):
        return NodeEditIntent(
            intent_type=IntentType.DELETE,
            original_text="삭제",
            simple_changes={"mood": "extreme", "lighting": 1, "contrast": 10},
            overall_confidence=0.3,
        )
    
    # 기본 평가 테스트
    def test_evaluate_simple_intent(self, evaluator, simple_intent):
        """간단한 의도 평가"""
        result = evaluator.evaluate_intent(simple_intent)
        
        assert result is not None
        assert result.score > 0
        assert result.grade is not None
        assert result.action is not None
    
    def test_evaluate_returns_stpf_result(self, evaluator, simple_intent):
        """STPF 결과 포함"""
        result = evaluator.evaluate_intent(simple_intent)
        
        assert result.stpf_result is not None
        assert result.stpf_result.score_1000 == result.score
    
    def test_evaluate_includes_kelly(self, evaluator, simple_intent):
        """Kelly 권장 포함"""
        result = evaluator.evaluate_intent(simple_intent)
        
        assert result.kelly_recommendation is not None
    
    def test_evaluate_includes_risk_breakdown(self, evaluator, simple_intent):
        """리스크 분석 포함"""
        result = evaluator.evaluate_intent(simple_intent)
        
        assert result.risk_breakdown is not None
        assert result.total_risk >= 0
    
    # 행동 결정 테스트
    def test_simple_change_not_rejected(self, evaluator, simple_intent):
        """간단한 변경은 거부되지 않음"""
        result = evaluator.evaluate_intent(simple_intent)
        
        assert result.action != GradeAction.REJECT
    
    def test_risky_intent_higher_risk(self, evaluator, simple_intent, risky_intent):
        """위험한 의도는 더 높은 리스크"""
        simple_result = evaluator.evaluate_intent(simple_intent)
        risky_result = evaluator.evaluate_intent(risky_intent)
        
        assert risky_result.total_risk > simple_result.total_risk
    
    def test_delete_intent_high_risk(self, evaluator):
        """삭제 의도는 높은 리스크"""
        intent = NodeEditIntent(
            intent_type=IntentType.DELETE,
            original_text="삭제",
            simple_changes={"node": "deleted"},
            overall_confidence=0.5,
        )
        
        result = evaluator.evaluate_intent(intent)
        assert result.total_risk > 5  # 기본보다 높음
    
    # 직접 변경 평가
    def test_evaluate_changes_directly(self, evaluator):
        """변경 직접 평가"""
        result = evaluator.evaluate_changes(
            {"mood": "dramatic", "lighting": 8},
            IntentType.MODIFY,
        )
        
        assert result is not None
        assert result.score > 0
    
    # 배치 평가
    def test_batch_evaluate(self, evaluator):
        """배치 평가"""
        intents = [
            NodeEditIntent(intent_type=IntentType.MODIFY, original_text="a", simple_changes={"a": 1}),
            NodeEditIntent(intent_type=IntentType.MODIFY, original_text="b", simple_changes={"b": 2}),
        ]
        
        results = evaluator.batch_evaluate(intents)
        assert len(results) == 2
        assert all(r.score > 0 for r in results)
    
    # 대안 제안 테스트
    def test_suggest_alternatives_for_rejected(self, evaluator, risky_intent):
        """거부된 경우 대안 제안"""
        # 낮은 점수 의도 평가
        result = evaluator.evaluate_intent(risky_intent)
        
        if result.action in [GradeAction.REJECT, GradeAction.SUGGEST_ALTERNATIVE]:
            suggestions = evaluator.suggest_alternatives(risky_intent, result)
            # 높은 리스크 속성이 있으면 대안이 있어야 함
            if "mood" in risky_intent.to_simple_dict():
                assert len(suggestions) > 0
    
    def test_no_alternatives_for_approved(self, evaluator, simple_intent):
        """승인된 경우 대안 없음"""
        result = evaluator.evaluate_intent(simple_intent)
        
        if result.action not in [GradeAction.REJECT, GradeAction.SUGGEST_ALTERNATIVE]:
            suggestions = evaluator.suggest_alternatives(simple_intent, result)
            assert len(suggestions) == 0
    
    # 유틸리티 테스트
    def test_get_grade_thresholds(self, evaluator):
        """Grade 임계값 조회"""
        thresholds = evaluator.get_grade_thresholds()
        
        assert "unicorn" in thresholds
        assert "high_potential" in thresholds
        assert "red_ocean" in thresholds
        assert "death_valley" in thresholds
    
    def test_stats(self, evaluator, simple_intent):
        """통계"""
        evaluator.evaluate_intent(simple_intent)
        stats = evaluator.get_stats()
        
        assert stats["total_evaluations"] >= 1
        assert "reject_rate" in stats


class TestNodeSTPFIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스"""
        assert node_stpf_evaluator is not None
        assert isinstance(node_stpf_evaluator, NodeSTPFEvaluator)
    
    def test_grade_action_values(self):
        """GradeAction 값"""
        assert GradeAction.AUTO_APPLY.value == "auto_apply"
        assert GradeAction.REJECT.value == "reject"
    
    def test_full_evaluation_cycle(self):
        """전체 평가 사이클"""
        evaluator = NodeSTPFEvaluator()
        
        # 1. 간단한 변경
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="극적으로",
            simple_changes={"mood": "dramatic"},
            overall_confidence=0.85,
        )
        
        result = evaluator.evaluate_intent(intent)
        
        # 2. 결과 확인
        assert result.score > 0
        assert result.action is not None
        assert result.action_reason is not None
        
        # 3. Kelly 확인
        if result.kelly_fraction is not None:
            assert 0 <= result.kelly_fraction <= 1
        
        # 4. 리스크 확인
        assert "intent_type" in result.risk_breakdown
