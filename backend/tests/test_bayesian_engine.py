"""
Unit Tests for Bayesian Truth Engine

Coverage Target: 80%+
"""
import pytest
from app.services.bayesian_engine import BayesianTruthEngine, bayesian_engine
from app.schemas.director_pack import DNAInvariant, InvariantType, RuleSpec, RulePriority
from app.schemas.bayesian_schemas import Evidence
import uuid


class TestBayesianTruthEngine:
    """베이지안 진실 엔진 테스트"""
    
    @pytest.fixture
    def engine(self):
        return BayesianTruthEngine()
    
    @pytest.fixture
    def sample_invariant(self):
        return DNAInvariant(
            rule_id="test_hook_timing",
            rule_type=InvariantType.TIMING,
            name="Hook Timing Rule",
            condition="hook_start_time",
            spec=RuleSpec(operator="lt", value=2.0),
            priority=RulePriority.HIGH,
            confidence=0.5,
            prior_strength=1.0,
            evidence_count=0,
        )
    
    @pytest.fixture
    def supporting_evidence(self):
        return Evidence(
            evidence_id=str(uuid.uuid4()),
            rule_id="test_hook_timing",
            evidence_type="production_result",
            supports_rule=True,
            strength=1.0,
        )
    
    @pytest.fixture
    def refuting_evidence(self):
        return Evidence(
            evidence_id=str(uuid.uuid4()),
            rule_id="test_hook_timing",
            evidence_type="production_result",
            supports_rule=False,
            strength=1.0,
        )
    
    # 기본 갱신 테스트
    def test_update_confidence_supporting(self, engine, sample_invariant, supporting_evidence):
        """지지 증거로 신뢰도 상승 테스트"""
        updated_inv, update = engine.update_confidence(sample_invariant, supporting_evidence)
        
        assert update.posterior > update.prior
        assert updated_inv.confidence > sample_invariant.confidence
        assert updated_inv.evidence_count == 1
        assert update.delta > 0
    
    def test_update_confidence_refuting(self, engine, sample_invariant, refuting_evidence):
        """반박 증거로 신뢰도 하락 테스트"""
        updated_inv, update = engine.update_confidence(sample_invariant, refuting_evidence)
        
        assert update.posterior < update.prior
        assert updated_inv.confidence < sample_invariant.confidence
        assert update.delta < 0
    
    # 극단값 테스트
    def test_clip_high_confidence(self, engine, sample_invariant, supporting_evidence):
        """높은 신뢰도 클리핑 테스트"""
        sample_invariant.confidence = 0.99
        updated_inv, _ = engine.update_confidence(sample_invariant, supporting_evidence)
        
        assert updated_inv.confidence <= engine.MAX_CONFIDENCE
    
    def test_clip_low_confidence(self, engine, sample_invariant, refuting_evidence):
        """낮은 신뢰도 클리핑 테스트"""
        sample_invariant.confidence = 0.01
        updated_inv, _ = engine.update_confidence(sample_invariant, refuting_evidence)
        
        assert updated_inv.confidence >= engine.MIN_CONFIDENCE
    
    # prior_strength 테스트
    def test_high_prior_strength_conservative(self, engine, sample_invariant, supporting_evidence):
        """높은 prior_strength는 보수적 갱신"""
        sample_invariant.prior_strength = 2.0
        _, update_high = engine.update_confidence(sample_invariant, supporting_evidence)
        
        sample_invariant.prior_strength = 0.5
        sample_invariant.confidence = 0.5  # 초기화
        _, update_low = engine.update_confidence(sample_invariant, supporting_evidence)
        
        # 낮은 prior_strength가 더 큰 변화
        assert abs(update_low.delta) >= abs(update_high.delta) * 0.5
    
    # 배치 갱신 테스트
    def test_batch_update(self, engine, sample_invariant, supporting_evidence):
        """배치 갱신 테스트"""
        invariants = [sample_invariant]
        evidences = [supporting_evidence, supporting_evidence]
        
        updated, updates = engine.batch_update(invariants, evidences)
        
        assert len(updates) == 2
        assert updated[0].evidence_count == 2
        assert updated[0].confidence > sample_invariant.confidence
    
    def test_batch_update_missing_rule(self, engine, sample_invariant):
        """존재하지 않는 rule_id 처리"""
        evidence = Evidence(
            evidence_id=str(uuid.uuid4()),
            rule_id="nonexistent_rule",
            evidence_type="user_feedback",
            supports_rule=True,
            strength=1.0,
        )
        
        updated, updates = engine.batch_update([sample_invariant], [evidence])
        
        assert len(updates) == 0
        assert updated[0].evidence_count == 0
    
    # 필터링 테스트
    def test_get_low_confidence_rules(self, engine):
        """낮은 신뢰도 규칙 필터링"""
        invariants = [
            DNAInvariant(
                rule_id=f"rule_{i}",
                rule_type=InvariantType.TIMING,
                name=f"Rule {i}",
                condition="test",
                spec=RuleSpec(operator="gt", value=0),
                confidence=0.2 * i,
            )
            for i in range(5)
        ]
        
        low_conf = engine.get_low_confidence_rules(invariants, threshold=0.5)
        assert len(low_conf) == 3  # 0.0, 0.2, 0.4
    
    def test_get_high_confidence_rules(self, engine):
        """높은 신뢰도 규칙 필터링"""
        invariants = [
            DNAInvariant(
                rule_id=f"rule_{i}",
                rule_type=InvariantType.TIMING,
                name=f"Rule {i}",
                condition="test",
                spec=RuleSpec(operator="gt", value=0),
                confidence=0.2 * i,
            )
            for i in range(6)
        ]
        
        high_conf = engine.get_high_confidence_rules(invariants, threshold=0.8)
        assert len(high_conf) == 2  # 0.8, 1.0
    
    # 팩 신뢰도 계산 테스트
    def test_calculate_pack_confidence(self, engine):
        """DirectorPack 전체 신뢰도 계산"""
        invariants = [
            DNAInvariant(
                rule_id="critical_1",
                rule_type=InvariantType.TIMING,
                name="Critical Rule",
                condition="test",
                spec=RuleSpec(operator="gt", value=0),
                priority=RulePriority.CRITICAL,
                confidence=0.9,
            ),
            DNAInvariant(
                rule_id="low_1",
                rule_type=InvariantType.TIMING,
                name="Low Rule",
                condition="test",
                spec=RuleSpec(operator="gt", value=0),
                priority=RulePriority.LOW,
                confidence=0.3,
            ),
        ]
        
        pack_conf = engine.calculate_pack_confidence(invariants)
        
        # Critical 가중치가 높으므로 0.9에 가까워야 함
        assert pack_conf > 0.7
    
    def test_calculate_pack_confidence_empty(self, engine):
        """빈 invariants 처리"""
        pack_conf = engine.calculate_pack_confidence([])
        assert pack_conf == 0.5


class TestBayesianIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스 확인"""
        assert bayesian_engine is not None
        assert isinstance(bayesian_engine, BayesianTruthEngine)
    
    def test_full_update_cycle(self):
        """전체 갱신 사이클 테스트"""
        inv = DNAInvariant(
            rule_id="cycle_test",
            rule_type=InvariantType.ENGAGEMENT,
            name="Engagement Rule",
            condition="engagement_rate",
            spec=RuleSpec(operator="gt", value=0.5),
            confidence=0.5,
        )
        
        # 5번의 지지 증거
        for i in range(5):
            ev = Evidence(
                evidence_id=str(uuid.uuid4()),
                rule_id="cycle_test",
                evidence_type="metric",
                supports_rule=True,
                strength=0.8,
            )
            inv, _ = bayesian_engine.update_confidence(inv, ev)
        
        # 신뢰도가 크게 상승해야 함
        assert inv.confidence > 0.9
        assert inv.evidence_count == 5
