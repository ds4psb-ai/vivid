"""
Unit Tests for Kelly-Based Credit Allocator

Coverage Target: 80%+
"""
import pytest
from app.services.kelly_allocator import KellyBasedCreditAllocator, kelly_allocator


class TestKellyBasedCreditAllocator:
    """Kelly 기반 크레딧 배분 테스트"""
    
    @pytest.fixture
    def allocator(self):
        return KellyBasedCreditAllocator()
    
    # Kelly Criterion 계산 테스트
    def test_kelly_positive_edge(self, allocator):
        """양수 에지 (투자 권장)"""
        result = allocator.calculate_kelly(success_probability=0.7, reward_ratio=2.0)
        
        assert result.f_star > 0
        assert result.f_safe > 0
        assert result.edge > 0
        assert "투자" in result.recommendation
    
    def test_kelly_negative_edge(self, allocator):
        """음수 에지 (투자 비권장)"""
        result = allocator.calculate_kelly(success_probability=0.2, reward_ratio=1.0)
        
        assert result.f_star < 0
        assert result.f_safe == 0
        assert result.edge < 0
        assert "마세요" in result.recommendation
    
    def test_kelly_break_even(self, allocator):
        """손익분기점 (p = 1/(1+b))"""
        # b=2.0일 때 손익분기점은 p=1/3=0.333...
        result = allocator.calculate_kelly(success_probability=0.34, reward_ratio=2.0)
        
        # 거의 0에 가까운 에지
        assert abs(result.edge) < 0.1
    
    def test_kelly_high_probability(self, allocator):
        """높은 성공 확률"""
        result = allocator.calculate_kelly(success_probability=0.9, reward_ratio=2.0)
        
        assert result.f_star > 0.5
        assert result.f_safe >= 0.25
        assert "적극" in result.recommendation
    
    def test_kelly_fractional(self, allocator):
        """Fractional Kelly (50%) 적용 확인"""
        result = allocator.calculate_kelly(success_probability=0.8, reward_ratio=2.0)
        
        # f_safe는 f_star의 50%
        assert result.f_safe == pytest.approx(result.f_star * 0.5, abs=0.01)
    
    # 극단값 클리핑 테스트
    def test_clip_probability(self, allocator):
        """확률 클리핑"""
        result_low = allocator.calculate_kelly(success_probability=0.0, reward_ratio=2.0)
        result_high = allocator.calculate_kelly(success_probability=1.0, reward_ratio=2.0)
        
        assert result_low.success_probability >= allocator.MIN_PROB
        assert result_high.success_probability <= allocator.MAX_PROB
    
    def test_clip_reward_ratio(self, allocator):
        """보상 비율 0 방지"""
        result = allocator.calculate_kelly(success_probability=0.5, reward_ratio=0.0)
        
        # 분모 0 방지
        assert result.reward_ratio >= 0.01
    
    # 크레딧 배분 테스트
    def test_allocation_normal(self, allocator):
        """정상 배분"""
        result = allocator.calculate_allocation(
            user_balance=1000,
            base_cost=10,
            success_probability=0.7,
            reward_ratio=2.0,
        )
        
        assert result.max_safe_investment <= 1000
        assert result.max_safe_investment > 0
        assert result.recommended_runs >= 1
        assert result.bankruptcy_probability < 0.05
    
    def test_allocation_low_balance(self, allocator):
        """낮은 잔액"""
        result = allocator.calculate_allocation(
            user_balance=50,
            base_cost=10,
            success_probability=0.7,
            reward_ratio=2.0,
        )
        
        assert result.recommended_runs >= 1
        assert result.max_safe_investment <= 50
    
    def test_allocation_high_cost(self, allocator):
        """높은 비용"""
        result = allocator.calculate_allocation(
            user_balance=100,
            base_cost=200,
            success_probability=0.7,
            reward_ratio=2.0,
        )
        
        assert result.recommended_runs >= 1  # 최소 1회
    
    def test_allocation_zero_cost(self, allocator):
        """비용 0 처리"""
        result = allocator.calculate_allocation(
            user_balance=1000,
            base_cost=0,
            success_probability=0.7,
            reward_ratio=2.0,
        )
        
        assert result.recommended_runs >= 1
    
    # 파산 확률 테스트
    def test_bankruptcy_high_prob(self, allocator):
        """높은 성공 확률 → 낮은 파산률"""
        result = allocator.calculate_allocation(
            user_balance=1000,
            base_cost=10,
            success_probability=0.8,
            reward_ratio=2.0,
        )
        
        assert result.bankruptcy_probability < 0.01
    
    def test_bankruptcy_low_prob(self, allocator):
        """낮은 성공 확률 → 높은 파산률"""
        result = allocator.calculate_allocation(
            user_balance=1000,
            base_cost=10,
            success_probability=0.4,
            reward_ratio=2.0,
        )
        
        assert result.bankruptcy_probability >= 0.5
    
    # 투자 결정 테스트
    def test_should_invest_positive(self, allocator):
        """투자 권장"""
        assert allocator.should_invest(success_probability=0.7, reward_ratio=2.0)
    
    def test_should_invest_negative(self, allocator):
        """투자 비권장"""
        assert not allocator.should_invest(success_probability=0.2, reward_ratio=1.0)
    
    # 최적 배치 크기 테스트
    def test_optimal_batch_size(self, allocator):
        """최적 배치 크기 (파산률 5% 이하)"""
        batch_size = allocator.calculate_optimal_batch_size(
            user_balance=1000,
            base_cost=10,
            success_probability=0.8,
            target_ruin_prob=0.05,
        )
        
        assert batch_size >= 1
        assert batch_size * 10 <= 1000  # 잔액 초과 안 함
    
    def test_optimal_batch_negative_edge(self, allocator):
        """음수 에지 → 최소 배치"""
        batch_size = allocator.calculate_optimal_batch_size(
            user_balance=1000,
            base_cost=10,
            success_probability=0.2,
            target_ruin_prob=0.05,
        )
        
        assert batch_size == 1
    
    # 모델 비용 테스트
    def test_get_model_cost(self, allocator):
        """모델별 비용 조회"""
        assert allocator.get_model_cost("gemini-2.0-flash-exp") == 10
        assert allocator.get_model_cost("veo-3.1") == 120
        assert allocator.get_model_cost("unknown_model") == 10  # 기본값


class TestKellyIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스 확인"""
        assert kelly_allocator is not None
        assert isinstance(kelly_allocator, KellyBasedCreditAllocator)
    
    def test_full_allocation_cycle(self):
        """전체 배분 사이클"""
        # 시뮬레이션: 1000 크레딧으로 veo-3.1 사용
        balance = 1000
        cost = kelly_allocator.get_model_cost("veo-3.1")
        
        result = kelly_allocator.calculate_allocation(
            user_balance=balance,
            base_cost=cost,
            success_probability=0.75,
            reward_ratio=3.0,
        )
        
        # 합리적인 배분 확인
        assert result.max_safe_investment <= balance
        assert result.max_safe_investment >= cost  # 최소 1회 실행 가능
        assert result.bankruptcy_probability < 0.15  # veo-3.1 is expensive, slightly higher threshold
