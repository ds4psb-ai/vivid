"""
Pattern Truth MCP Server

패턴 신뢰도 분석 및 STPF 통합 MCP 서버.
Bayesian 갱신과 Kelly 배분을 MCP 도구로 제공.

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.mcp_servers import MCPServerBase, mcp_tool, mcp_resource
from app.services.stpf_engine import STPFv31Engine
from app.services.bayesian_engine import BayesianTruthEngine
from app.services.kelly_allocator import KellyBasedCreditAllocator
from app.schemas.stpf_schemas import STPFInputs
from app.schemas.director_pack import DNAInvariant, InvariantType, RuleSpec, RulePriority
from app.schemas.bayesian_schemas import Evidence
import uuid

logger = logging.getLogger(__name__)


class PatternTruthMCP(MCPServerBase):
    """
    Pattern Truth MCP 서버
    
    제공 도구:
    - compute_stpf: STPF v3.1 점수 계산
    - analyze_sensitivity: 민감도 분석
    - update_confidence: 베이지안 신뢰도 갱신
    - calculate_kelly: Kelly 크레딧 배분
    """
    
    def __init__(self):
        super().__init__(name="pattern-truth", version="1.0.0")
        self.stpf = STPFv31Engine()
        self.bayesian = BayesianTruthEngine()
        self.kelly = KellyBasedCreditAllocator()
    
    def get_server_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": "패턴 신뢰도 분석 및 Computational Truth 엔진",
            "protocol": "streamable-http",
            "tools": len(self._tools),
            "resources": len(self._resources),
        }
    
    # =========================================================================
    # STPF Tools
    # =========================================================================
    
    @mcp_tool(
        name="compute_stpf",
        description="STPF v3.1 점수 계산 - 사업/프로젝트 평가",
        parameters={
            "trust": "신뢰도 (1-10)",
            "legality": "합법성 (1-10)",
            "hygiene": "위생 (1-10)",
            "essence": "본질 (1-10)",
            "capability": "역량 (1-10)",
            "novelty": "신규성 (1-10)",
            "proof": "증거 (1-10)",
            "cost": "비용 (1-10)",
            "risk": "위험 (1-10)",
            "uncertainty": "불확실성 (1-10)",
        }
    )
    async def compute_stpf(
        self,
        trust: float = 5.0,
        legality: float = 8.0,
        hygiene: float = 6.0,
        essence: float = 5.0,
        capability: float = 5.0,
        novelty: float = 5.0,
        connection: float = 5.0,
        proof: float = 5.0,
        cost: float = 5.0,
        risk: float = 5.0,
        threat: float = 5.0,
        pressure: float = 5.0,
        lag: float = 5.0,
        uncertainty: float = 5.0,
        network: float = 5.0,
        scarcity: float = 5.0,
        leverage: float = 5.0,
        expectation: float = 5.0,
        reality: float = 5.0,
    ) -> Dict[str, Any]:
        """STPF v3.1 점수 계산"""
        inputs = STPFInputs(
            trust=trust, legality=legality, hygiene=hygiene,
            essence=essence, capability=capability, novelty=novelty,
            connection=connection, proof=proof,
            cost=cost, risk=risk, threat=threat,
            pressure=pressure, lag=lag, uncertainty=uncertainty,
            network=network, scarcity=scarcity, leverage=leverage,
            expectation=expectation, reality=reality,
        )
        
        result = self.stpf.compute(inputs)
        
        return {
            "status": result.status,
            "score": round(result.score_1000, 1),
            "grade": result.grade,
            "p_success": round(result.p_success, 3),
            "kelly_f_safe": result.kelly.f_safe,
            "recommendation": self._get_recommendation(result.score_1000),
        }
    
    @mcp_tool(
        name="analyze_sensitivity",
        description="STPF 민감도 분석 - 레버리지 포인트 및 치명적 마찰 식별",
    )
    async def analyze_sensitivity(
        self,
        trust: float = 5.0,
        legality: float = 8.0,
        hygiene: float = 6.0,
        essence: float = 5.0,
        capability: float = 5.0,
        novelty: float = 5.0,
        connection: float = 5.0,
        proof: float = 5.0,
        cost: float = 5.0,
        risk: float = 5.0,
        threat: float = 5.0,
        pressure: float = 5.0,
        lag: float = 5.0,
        uncertainty: float = 5.0,
    ) -> Dict[str, Any]:
        """민감도 분석"""
        inputs = STPFInputs(
            trust=trust, legality=legality, hygiene=hygiene,
            essence=essence, capability=capability, novelty=novelty,
            connection=connection, proof=proof,
            cost=cost, risk=risk, threat=threat,
            pressure=pressure, lag=lag, uncertainty=uncertainty,
        )
        
        result = self.stpf.sensitivity(inputs)
        
        return {
            "status": result.status,
            "base_score": round(result.base_score, 1),
            "leverage_point": result.leverage_point,
            "fatal_friction": result.fatal_friction,
            "action_plan": self._get_action_plan(result),
        }
    
    # =========================================================================
    # Bayesian Tools
    # =========================================================================
    
    @mcp_tool(
        name="update_confidence",
        description="베이지안 신뢰도 갱신 - DNAInvariant confidence 업데이트",
        parameters={
            "rule_id": "규칙 ID",
            "supports_rule": "규칙 지지 여부",
            "strength": "증거 강도 (0-1)",
            "prior_confidence": "사전 신뢰도 (0-1)",
        }
    )
    async def update_confidence(
        self,
        rule_id: str,
        supports_rule: bool = True,
        strength: float = 0.8,
        prior_confidence: float = 0.5,
        prior_strength: float = 1.0,
    ) -> Dict[str, Any]:
        """베이지안 신뢰도 갱신"""
        # 테스트용 invariant 생성
        invariant = DNAInvariant(
            rule_id=rule_id,
            rule_type=InvariantType.TIMING,
            name=f"Rule {rule_id}",
            condition="test",
            spec=RuleSpec(operator="gt", value=0),
            confidence=prior_confidence,
            prior_strength=prior_strength,
        )
        
        evidence = Evidence(
            evidence_id=str(uuid.uuid4()),
            rule_id=rule_id,
            evidence_type="production_result",
            supports_rule=supports_rule,
            strength=strength,
        )
        
        updated, update = self.bayesian.update_confidence(invariant, evidence)
        
        return {
            "rule_id": rule_id,
            "prior": round(update.prior, 3),
            "posterior": round(update.posterior, 3),
            "delta": round(update.delta, 3),
            "evidence_count": update.evidence_count,
            "interpretation": self._interpret_confidence(update.posterior),
        }
    
    # =========================================================================
    # Kelly Tools
    # =========================================================================
    
    @mcp_tool(
        name="calculate_kelly",
        description="Kelly Criterion 크레딧 배분 - 최적 투자 비율 계산",
        parameters={
            "balance": "현재 잔액",
            "cost_per_run": "실행당 비용",
            "success_probability": "성공 확률 (0-1)",
            "reward_ratio": "보상 비율",
        }
    )
    async def calculate_kelly(
        self,
        balance: int = 1000,
        cost_per_run: int = 10,
        success_probability: float = 0.6,
        reward_ratio: float = 2.0,
    ) -> Dict[str, Any]:
        """Kelly 크레딧 배분"""
        result = self.kelly.calculate_allocation(
            user_balance=balance,
            base_cost=cost_per_run,
            success_probability=success_probability,
            reward_ratio=reward_ratio,
        )
        
        return {
            "kelly_fraction": round(result.kelly.f_safe, 3),
            "max_safe_investment": result.max_safe_investment,
            "recommended_runs": result.recommended_runs,
            "bankruptcy_probability": round(result.bankruptcy_probability, 4),
            "recommendation": result.kelly.recommendation,
            "should_invest": result.kelly.f_star > 0,
        }
    
    # =========================================================================
    # Resources
    # =========================================================================
    
    @mcp_resource(
        uri="pattern://health",
        name="Health Check",
        description="서버 상태 확인",
    )
    async def health_resource(self) -> Dict[str, Any]:
        """서버 상태"""
        return {
            "status": "healthy",
            "server": self.name,
            "version": self.version,
            "tools": self.list_tools(),
        }
    
    @mcp_resource(
        uri="pattern://config",
        name="Configuration",
        description="현재 설정",
    )
    async def config_resource(self) -> Dict[str, Any]:
        """설정 정보"""
        return {
            "stpf": {
                "log_mid": self.stpf.LOG_MID,
                "score_k": self.stpf.SCORE_K,
                "friction_exp": self.stpf.FRICTION_EXP,
            },
            "bayesian": {
                "min_confidence": self.bayesian.MIN_CONFIDENCE,
                "max_confidence": self.bayesian.MAX_CONFIDENCE,
            },
            "kelly": {
                "fraction": self.kelly.KELLY_FRACTION,
                "model_costs": self.kelly.DEFAULT_COSTS,
            },
        }
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _get_recommendation(self, score: float) -> str:
        """점수 기반 권장 사항"""
        if score >= 800:
            return "🚀 적극 투자 권장 - Unicorn Potential"
        elif score >= 500:
            return "✅ 투자 권장 - High Potential"
        elif score >= 250:
            return "⚠️ 신중히 검토 - Average"
        else:
            return "❌ 투자 보류 - Death Valley"
    
    def _get_action_plan(self, sensitivity) -> List[str]:
        """민감도 분석 기반 액션 플랜"""
        actions = []
        
        if sensitivity.leverage_point:
            var = sensitivity.leverage_point.get("var", "unknown")
            delta = sensitivity.leverage_point.get("delta", 0)
            actions.append(f"📈 {var} 강화 (+{delta:.1f} 점수 상승 예상)")
        
        if sensitivity.fatal_friction:
            var = sensitivity.fatal_friction.get("var", "unknown")
            delta = sensitivity.fatal_friction.get("delta", 0)
            actions.append(f"📉 {var} 감소 (+{delta:.1f} 점수 상승 예상)")
        
        return actions or ["현재 균형 상태"]
    
    def _interpret_confidence(self, confidence: float) -> str:
        """신뢰도 해석"""
        if confidence >= 0.9:
            return "매우 높음 - 검증된 규칙"
        elif confidence >= 0.7:
            return "높음 - 신뢰할 수 있음"
        elif confidence >= 0.5:
            return "보통 - 추가 증거 필요"
        elif confidence >= 0.3:
            return "낮음 - 재검토 권장"
        else:
            return "매우 낮음 - 규칙 폐기 검토"


# 싱글톤 인스턴스
pattern_truth_mcp = PatternTruthMCP()
