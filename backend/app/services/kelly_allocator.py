"""
Kelly-Based Credit Allocator

Kelly Criterion 기반 크레딧 배분 서비스.
성공 확률과 보상 비율을 기반으로 최적 투자 비율 계산.

수학적 기반:
f* = (bp - q) / b
- b: odds (reward ratio)
- p: 성공 확률
- q: 실패 확률 (1 - p)

License: arkain.info@gmail.com (Gemini Enterprise)
"""
import logging
from typing import Optional, Dict
from app.schemas.kelly_schemas import KellyResult, CreditAllocation

logger = logging.getLogger(__name__)


class KellyBasedCreditAllocator:
    """
    Kelly Criterion 기반 크레딧 배분
    
    Features:
    - 최적 투자 비율 계산
    - 파산 확률 추정
    - 보수적 (50%) Kelly 적용
    """
    
    # 안전 계수 (Fractional Kelly)
    KELLY_FRACTION = 0.5  # 50% Kelly - 더 보수적
    
    # 극단값 방지
    MIN_PROB = 0.01
    MAX_PROB = 0.99
    
    # 기본 크레딧 비용 (모델별)
    DEFAULT_COSTS: Dict[str, int] = {
        "gemini-3-flash-preview": 10,
        "gemini-3-pro-preview": 25,
        "veo-3.0": 100,
    }
    
    def calculate_kelly(
        self,
        success_probability: float,
        reward_ratio: float = 2.0,
    ) -> KellyResult:
        """
        Kelly Criterion 계산
        
        f* = (bp - q) / b
        
        Args:
            success_probability: 성공 확률 (p)
            reward_ratio: 보상 비율 (b = upside/downside)
        
        Returns:
            KellyResult with f_star, f_safe, recommendation
        """
        p = max(self.MIN_PROB, min(self.MAX_PROB, success_probability))
        q = 1 - p
        b = max(reward_ratio, 0.01)  # 분모 0 방지
        
        # Kelly formula
        edge = b * p - q
        f_star = edge / b
        
        # Fractional Kelly (보수적)
        f_safe = max(0, f_star * self.KELLY_FRACTION)
        
        # 권장 사항
        if f_star < 0:
            recommendation = "투자하지 마세요 (음수 에지)"
        elif f_safe < 0.05:
            recommendation = "최소 투자만 권장 (낮은 에지)"
        elif f_safe < 0.15:
            recommendation = "보수적 투자 권장"
        elif f_safe < 0.25:
            recommendation = "적정 투자 권장"
        else:
            recommendation = "적극적 투자 가능"
        
        result = KellyResult(
            success_probability=round(p, 4),
            reward_ratio=round(b, 2),
            f_star=round(f_star, 4),
            f_safe=round(f_safe, 4),
            edge=round(edge, 4),
            recommendation=recommendation
        )
        
        logger.info(
            f"Kelly: p={p:.3f}, b={b:.1f}, f*={f_star:.3f}, f_safe={f_safe:.3f}"
        )
        
        return result
    
    def calculate_allocation(
        self,
        user_balance: int,
        base_cost: int,
        success_probability: float,
        reward_ratio: float = 2.0,
    ) -> CreditAllocation:
        """
        크레딧 배분 계산
        
        Args:
            user_balance: 현재 잔여 크레딧
            base_cost: 단위 작업 비용
            success_probability: 성공 확률
            reward_ratio: 보상 비율
        
        Returns:
            CreditAllocation with max_safe_investment, recommended_runs
        """
        kelly = self.calculate_kelly(success_probability, reward_ratio)
        
        # 최대 안전 투자액
        max_safe_investment = int(user_balance * kelly.f_safe)
        
        # 권장 실행 횟수 (최소 1회)
        if base_cost > 0:
            recommended_runs = max(1, max_safe_investment // base_cost)
        else:
            recommended_runs = 1
        
        # 파산 확률 추정 (간단한 근사)
        # P(ruin) ≈ ((1-p)/p)^n where n = runs
        if success_probability > 0.5:
            ruin_prob = ((1 - success_probability) / success_probability) ** recommended_runs
            ruin_prob = min(ruin_prob, 1.0)
        else:
            ruin_prob = 0.5  # 50% 이하면 기본 0.5
        
        allocation = CreditAllocation(
            user_balance=user_balance,
            base_cost=base_cost,
            kelly=kelly,
            max_safe_investment=max_safe_investment,
            recommended_runs=recommended_runs,
            bankruptcy_probability=round(ruin_prob, 4)
        )
        
        logger.info(
            f"Allocation: balance={user_balance}, max_invest={max_safe_investment}, "
            f"runs={recommended_runs}, ruin_prob={ruin_prob:.4f}"
        )
        
        return allocation
    
    def get_model_cost(self, model: str) -> int:
        """모델별 기본 크레딧 비용 조회"""
        return self.DEFAULT_COSTS.get(model, 10)
    
    def should_invest(
        self,
        success_probability: float,
        reward_ratio: float = 2.0,
    ) -> bool:
        """투자 여부 판단 (양수 에지 확인)"""
        kelly = self.calculate_kelly(success_probability, reward_ratio)
        return kelly.f_star > 0
    
    def calculate_optimal_batch_size(
        self,
        user_balance: int,
        base_cost: int,
        success_probability: float,
        reward_ratio: float = 2.0,
        target_ruin_prob: float = 0.05,
    ) -> int:
        """
        목표 파산 확률을 만족하는 최대 배치 크기 계산
        
        Kelly 기준으로 파산 확률 5% 이하 유지
        """
        kelly = self.calculate_kelly(success_probability, reward_ratio)
        
        if kelly.f_safe <= 0 or base_cost <= 0:
            return 1
        
        max_investment = int(user_balance * kelly.f_safe)
        max_runs = max(1, max_investment // base_cost)
        
        # 파산 확률 체크하며 줄이기
        for runs in range(max_runs, 0, -1):
            if success_probability > 0.5:
                ruin_prob = ((1 - success_probability) / success_probability) ** runs
                if ruin_prob <= target_ruin_prob:
                    return runs
        
        return 1


# 싱글톤 인스턴스
kelly_allocator = KellyBasedCreditAllocator()
