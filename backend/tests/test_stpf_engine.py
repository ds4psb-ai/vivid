"""
Unit Tests for STPF v3.1 Engine

Coverage Target: 80%+
"""
import pytest
from app.services.stpf_engine import STPFv31Engine
from app.schemas.stpf_schemas import STPFInputs


class TestSTPFv31Engine:
    """STPF v3.1 Safe Math 엔진 테스트"""
    
    @pytest.fixture
    def engine(self):
        return STPFv31Engine()
    
    @pytest.fixture
    def valid_inputs(self):
        return STPFInputs(
            trust=7, legality=8, hygiene=6,
            essence=7, capability=6, novelty=5, connection=5, proof=6,
            cost=5, risk=6, threat=5, pressure=5, lag=5, uncertainty=4,
            network=5, scarcity=5, leverage=5,
            expectation=5, reality=5,
        )
    
    @pytest.fixture
    def gate_fail_inputs(self):
        return STPFInputs(
            trust=3, legality=8, hygiene=6,  # trust < 4
            essence=7, capability=6, novelty=5, connection=5, proof=6,
            cost=5, risk=6, threat=5, pressure=5, lag=5, uncertainty=4,
        )
    
    # 기본 계산 테스트
    def test_compute_valid(self, engine, valid_inputs):
        """정상 입력 계산"""
        result = engine.compute(valid_inputs)
        
        assert result.status == "OK"
        assert result.score_1000 > 0
        assert result.score_1000 <= 1000
        assert result.p_success > 0
        assert result.p_success < 1
        assert result.grade is not None
    
    def test_compute_gate_fail(self, engine, gate_fail_inputs):
        """게이트 실패 (Kill Switch)"""
        result = engine.compute(gate_fail_inputs)
        
        assert result.status == "GATE_FAIL"
        assert result.score_1000 == 0
    
    # 점수 범위 테스트
    def test_score_range(self, engine):
        """점수 0-1000 범위"""
        # 최소 점수 (높은 friction)
        min_inputs = STPFInputs(
            trust=4, legality=4, hygiene=4,
            essence=1, capability=1, novelty=1, connection=1, proof=1,
            cost=10, risk=10, threat=10, pressure=10, lag=10, uncertainty=10,
        )
        min_result = engine.compute(min_inputs)
        
        # 최대 점수 (낮은 friction)
        max_inputs = STPFInputs(
            trust=10, legality=10, hygiene=10,
            essence=10, capability=10, novelty=10, connection=10, proof=10,
            cost=1, risk=1, threat=1, pressure=1, lag=1, uncertainty=1,
        )
        max_result = engine.compute(max_inputs)
        
        assert 0 <= min_result.score_1000 <= 1000
        assert 0 <= max_result.score_1000 <= 1000
        assert max_result.score_1000 > min_result.score_1000
    
    # Sensitivity 분석 테스트
    def test_sensitivity(self, engine, valid_inputs):
        """감도 분석"""
        result = engine.sensitivity(valid_inputs)
        
        assert result.status == "OK"
        assert result.base_score >= 0
        assert result.leverage_point is not None
        assert result.fatal_friction is not None
    
    # 시나리오 분석 테스트
    def test_scenarios(self, engine, valid_inputs):
        """3분기 시나리오 분석"""
        result = engine.scenarios(valid_inputs)
        
        assert result.worst.score_1000 <= result.base.score_1000 <= result.best.score_1000
        assert result.final_recommendation_score > 0
    
    # 등급 분류 테스트
    def test_grade_classification(self, engine):
        """등급 분류 테스트"""
        # Death Valley (낮은 점수)
        inputs_low = STPFInputs(
            trust=4, legality=4, hygiene=4,
            essence=2, capability=2, novelty=2, connection=2, proof=2,
            cost=8, risk=8, threat=8, pressure=8, lag=8, uncertainty=8,
        )
        result_low = engine.compute(inputs_low)
        assert result_low.grade in ["Death Valley", "Average"]
        
        # High Potential (높은 점수)
        inputs_high = STPFInputs(
            trust=8, legality=8, hygiene=8,
            essence=8, capability=7, novelty=6, connection=7, proof=7,
            cost=3, risk=3, threat=3, pressure=3, lag=3, uncertainty=3,
        )
        result_high = engine.compute(inputs_high)
        assert result_high.grade in ["High Potential", "Unicorn", "Average"]


class TestSTPFIntegration:
    """통합 테스트"""
    
    def test_full_analysis_cycle(self):
        """전체 분석 사이클"""
        engine = STPFv31Engine()
        inputs = STPFInputs(
            trust=7, legality=8, hygiene=7,
            essence=8, capability=7, novelty=6, connection=6, proof=7,
            cost=4, risk=5, threat=4, pressure=4, lag=4, uncertainty=4,
        )
        
        # 1. 기본 계산
        compute_result = engine.compute(inputs)
        assert compute_result.status == "OK"
        assert compute_result.score_1000 > 0
        
        # 2. 감도 분석
        sensitivity_result = engine.sensitivity(inputs)
        assert sensitivity_result.leverage_point
        
        # 3. 시나리오 분석
        scenario_result = engine.scenarios(inputs)
        assert scenario_result.final_recommendation_score > 0
        
        # 결과 일관성 확인
        assert sensitivity_result.base_score == compute_result.score_1000
        assert scenario_result.base.score_1000 == compute_result.score_1000
