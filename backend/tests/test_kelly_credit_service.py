"""
Unit Tests for Kelly Credit Service

Coverage Target: 80%+
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.kelly_credit_service import (
    KellyIntegratedCreditService,
    kelly_credit_service,
    KellyDecision,
    ExecutionResult,
)


class TestKellyDecision:
    """KellyDecision 테스트"""
    
    def test_should_execute_true(self):
        """실행 허용"""
        decision = KellyDecision(
            should_execute=True,
            allocation=None,
            warning=None,
        )
        assert decision.should_execute is True
    
    def test_should_execute_false_with_warning(self):
        """실행 거부 + 경고"""
        decision = KellyDecision(
            should_execute=False,
            allocation=None,
            warning="잔액 부족",
        )
        assert decision.should_execute is False
        assert decision.warning == "잔액 부족"


class TestExecutionResult:
    """ExecutionResult 테스트"""
    
    def test_success_result(self):
        """성공 결과"""
        result = ExecutionResult(
            success=True,
            credits_used=10,
            feedback_sent=True,
            kelly_fraction=0.25,
            message="실행 완료",
        )
        assert result.success is True
        assert result.credits_used == 10
    
    def test_failure_result(self):
        """실패 결과"""
        result = ExecutionResult(
            success=False,
            credits_used=0,
            feedback_sent=False,
            kelly_fraction=0,
            message="실행 실패",
        )
        assert result.success is False
        assert result.credits_used == 0


class TestKellyIntegratedCreditService:
    """Kelly 통합 크레딧 서비스 테스트"""
    
    @pytest.fixture
    def service(self):
        return KellyIntegratedCreditService()
    
    def test_default_success_probs(self, service):
        """기본 성공 확률"""
        assert service.DEFAULT_SUCCESS_PROBS["gemini-2.5-flash"] == 0.75
        assert service.DEFAULT_SUCCESS_PROBS["veo-3.1"] == 0.7
    
    def test_max_bankruptcy_prob(self, service):
        """최대 파산 확률"""
        assert service.MAX_BANKRUPTCY_PROB == 0.05


class TestKellyIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스"""
        assert kelly_credit_service is not None
        assert isinstance(kelly_credit_service, KellyIntegratedCreditService)
    
    @pytest.mark.asyncio
    async def test_send_feedback(self):
        """피드백 전송"""
        service = KellyIntegratedCreditService()
        
        sent = await service._send_feedback(
            capsule_id="test_capsule",
            success=True,
            rule_ids=[],
            model="gemini-2.5-flash",
        )
        
        assert sent is True
    
    @pytest.mark.asyncio
    async def test_get_success_probability(self):
        """성공 확률 조회"""
        service = KellyIntegratedCreditService()
        
        # Mock DB session
        mock_db = AsyncMock()
        
        prob = await service._get_success_probability(
            db=mock_db,
            user_id="test_user",
            model="gemini-2.5-flash",
        )
        
        assert prob == 0.75  # 기본값
    
    @pytest.mark.asyncio
    async def test_get_success_probability_unknown_model(self):
        """알 수 없는 모델 성공 확률"""
        service = KellyIntegratedCreditService()
        mock_db = AsyncMock()
        
        prob = await service._get_success_probability(
            db=mock_db,
            user_id="test_user",
            model="unknown-model",
        )
        
        assert prob == 0.7  # fallback
