"""
Kelly-Integrated Credit Service

Kelly Criterion 기반 크레딧 배분 + 피드백 루프 통합 서비스.

Flow:
1. Kelly 배분 확인 (투자 권장 여부)
2. 크레딧 차감
3. 캡슐 실행
4. 결과에 따른 피드백 전송

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.credit_service import (
    get_or_create_user_credits,
    deduct_credits,
    refund_credits,
)
from app.services.kelly_allocator import kelly_allocator
from app.services.feedback_processor import feedback_processor
from app.schemas.feedback_schemas import ProductionResult, ResultOutcome
from app.schemas.kelly_schemas import CreditAllocation

logger = logging.getLogger(__name__)


@dataclass
class KellyDecision:
    """Kelly 배분 결정 결과"""
    should_execute: bool
    allocation: Optional[CreditAllocation]
    warning: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class ExecutionResult:
    """실행 결과 (크레딧 + 피드백)"""
    success: bool
    credits_used: int
    feedback_sent: bool
    kelly_fraction: float
    message: str


class KellyIntegratedCreditService:
    """
    Kelly 통합 크레딧 서비스
    
    Features:
    - 실행 전 Kelly 배분 확인
    - 최적 배치 크기 권장
    - 실행 후 자동 피드백
    - 파산 확률 관리
    """
    
    # 파산 확률 임계값
    MAX_BANKRUPTCY_PROB = 0.05
    
    # 모델별 기본 성공 확률 (초기값, 피드백으로 갱신)
    DEFAULT_SUCCESS_PROBS = {
        "gemini-2.0-flash-exp": 0.8,
        "gemini-3-flash-preview": 0.75,
        "gemini-2.5-pro": 0.85,
        "veo-3.1": 0.7,
    }
    
    async def check_kelly_allocation(
        self,
        db: AsyncSession,
        user_id: str,
        credit_cost: int,
        model: str = "gemini-3-flash-preview",
        reward_ratio: float = 2.0,
    ) -> KellyDecision:
        """
        캡슐 실행 전 Kelly 배분 확인
        
        Args:
            db: DB 세션
            user_id: 사용자 ID
            credit_cost: 실행 비용
            model: 사용 모델
            reward_ratio: 보상 비율
        
        Returns:
            KellyDecision with recommendation
        """
        # 1. 잔액 확인
        user_credits = await get_or_create_user_credits(db, user_id)
        balance = user_credits.balance
        
        if balance < credit_cost:
            return KellyDecision(
                should_execute=False,
                allocation=None,
                warning="잔액 부족",
                recommendation=f"필요: {credit_cost}, 잔액: {balance}",
            )
        
        # 2. 성공 확률 (피드백 기반 또는 기본값)
        success_prob = await self._get_success_probability(db, user_id, model)
        
        # 3. Kelly 배분 계산
        allocation = kelly_allocator.calculate_allocation(
            user_balance=balance,
            base_cost=credit_cost,
            success_probability=success_prob,
            reward_ratio=reward_ratio,
        )
        
        # 4. 결정
        should_execute = True
        warning = None
        
        # 파산 확률 체크
        if allocation.bankruptcy_probability > self.MAX_BANKRUPTCY_PROB:
            warning = f"파산 확률 {allocation.bankruptcy_probability:.1%} > {self.MAX_BANKRUPTCY_PROB:.0%}"
        
        # Kelly가 음수면 경고
        if allocation.kelly.f_star < 0:
            warning = "Kelly 에지 음수 - 투자 비권장"
        
        return KellyDecision(
            should_execute=should_execute,
            allocation=allocation,
            warning=warning,
            recommendation=allocation.kelly.recommendation,
        )
    
    async def execute_with_kelly(
        self,
        db: AsyncSession,
        user_id: str,
        credit_cost: int,
        capsule_id: str,
        model: str,
        execute_fn,  # async callable
        execute_args: Dict[str, Any],
        rule_ids: list[str] = None,
        byok_key: Optional[str] = None,
    ) -> Tuple[Any, ExecutionResult]:
        """
        Kelly 통합 캡슐 실행
        
        Args:
            db: DB 세션
            user_id: 사용자 ID
            credit_cost: 비용
            capsule_id: 캡슐 ID
            model: 모델
            execute_fn: 실행 함수
            execute_args: 실행 인자
            rule_ids: 관련 규칙 ID 목록
            byok_key: BYOK 키 (있으면 크레딧 차감 안 함)
        
        Returns:
            (실행 결과, ExecutionResult)
        """
        # 1. Kelly 확인
        kelly_decision = await self.check_kelly_allocation(
            db, user_id, credit_cost, model
        )
        
        # 2. 크레딧 차감 (BYOK 아닌 경우)
        credits_deducted = 0
        if not byok_key:
            if not kelly_decision.should_execute:
                return None, ExecutionResult(
                    success=False,
                    credits_used=0,
                    feedback_sent=False,
                    kelly_fraction=0,
                    message=kelly_decision.warning or "Kelly check failed",
                )
            
            await deduct_credits(
                db, user_id, credit_cost,
                description=f"Teaching: {capsule_id}",
                meta={
                    "capsule": capsule_id,
                    "model": model,
                    "kelly_fraction": kelly_decision.allocation.kelly.f_safe if kelly_decision.allocation else 0,
                }
            )
            credits_deducted = credit_cost
        
        # 3. 실행
        try:
            result = await execute_fn(**execute_args)
            success = result.get("success", False) if isinstance(result, dict) else bool(result)
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            success = False
            result = {"success": False, "error": str(e)}
            
            # 실패 시 환불
            if credits_deducted > 0:
                await refund_credits(
                    db, user_id, credits_deducted,
                    description=f"Refund: {capsule_id} failed",
                    meta={"error": str(e)[:200]}
                )
        
        # 4. 피드백 전송
        feedback_sent = await self._send_feedback(
            capsule_id=capsule_id,
            success=success,
            rule_ids=rule_ids or [],
            model=model,
        )
        
        return result, ExecutionResult(
            success=success,
            credits_used=credits_deducted if success else 0,
            feedback_sent=feedback_sent,
            kelly_fraction=kelly_decision.allocation.kelly.f_safe if kelly_decision.allocation else 0,
            message="실행 완료" if success else "실행 실패",
        )
    
    async def get_optimal_runs(
        self,
        db: AsyncSession,
        user_id: str,
        credit_cost: int,
        model: str = "gemini-3-flash-preview",
    ) -> Dict[str, Any]:
        """
        최적 실행 횟수 계산
        
        Returns:
            권장 실행 횟수 및 배분 정보
        """
        user_credits = await get_or_create_user_credits(db, user_id)
        success_prob = await self._get_success_probability(db, user_id, model)
        
        allocation = kelly_allocator.calculate_allocation(
            user_balance=user_credits.balance,
            base_cost=credit_cost,
            success_probability=success_prob,
            reward_ratio=2.0,
        )
        
        return {
            "balance": user_credits.balance,
            "cost_per_run": credit_cost,
            "success_probability": success_prob,
            "kelly_fraction": allocation.kelly.f_safe,
            "max_safe_investment": allocation.max_safe_investment,
            "recommended_runs": allocation.recommended_runs,
            "bankruptcy_probability": allocation.bankruptcy_probability,
            "recommendation": allocation.kelly.recommendation,
        }
    
    async def _get_success_probability(
        self,
        db: AsyncSession,
        user_id: str,
        model: str,
    ) -> float:
        """사용자/모델별 성공 확률 조회"""
        # TODO: 실제 피드백 데이터 기반 계산
        # 현재는 기본값 사용
        return self.DEFAULT_SUCCESS_PROBS.get(model, 0.7)
    
    async def _send_feedback(
        self,
        capsule_id: str,
        success: bool,
        rule_ids: list[str],
        model: str,
    ) -> bool:
        """피드백 루프에 결과 전송"""
        try:
            result = ProductionResult(
                capsule_id=capsule_id,
                outcome=ResultOutcome.SUCCESS if success else ResultOutcome.FAILURE,
                score=85.0 if success else 30.0,
                rule_ids=rule_ids,
                meta={"model": model},
            )
            
            feedback_processor.process_production_result(result)
            return True
        except Exception as e:
            logger.warning(f"Feedback send failed: {e}")
            return False


# 싱글톤 인스턴스
kelly_credit_service = KellyIntegratedCreditService()
