"""
Bayesian Truth Engine

실시간 베이지안 신뢰도 갱신 엔진.
DNAInvariant의 confidence를 증거 기반으로 갱신함.

수학적 기반:
P(Truth|Evidence) = P(Evidence|Truth) × P(Truth) / P(Evidence)

License: arkain.info@gmail.com (Gemini Enterprise)
"""
import logging
from typing import List, Optional, Tuple
from app.schemas.director_pack import DNAInvariant
from app.schemas.bayesian_schemas import Evidence, ConfidenceUpdate

logger = logging.getLogger(__name__)


class BayesianTruthEngine:
    """
    실시간 베이지안 신뢰도 갱신 엔진
    
    Features:
    - 증거 기반 DNAInvariant confidence 갱신
    - prior_strength에 따른 갱신 속도 조절
    - 안전한 수치 계산 (0/1 극단값 방지)
    """
    
    # 극단값 방지를 위한 클리핑
    MIN_CONFIDENCE = 0.01
    MAX_CONFIDENCE = 0.99
    
    # 기본 우도 값
    DEFAULT_LIKELIHOOD_SUPPORT = 0.9  # 규칙 지지 증거
    DEFAULT_LIKELIHOOD_REFUTE = 0.2   # 규칙 반박 증거
    
    def update_confidence(
        self,
        invariant: DNAInvariant,
        evidence: Evidence,
    ) -> Tuple[DNAInvariant, ConfidenceUpdate]:
        """
        베이지안 신뢰도 갱신
        
        P(H|E) = P(E|H) × P(H)^α / [P(E|H) × P(H)^α + P(E|¬H) × P(¬H)^α]
        
        α = prior_strength (갱신 속도 조절)
        - α > 1: 보수적 (기존 믿음 유지)
        - α < 1: 민감 (새 증거에 빠르게 반응)
        - α = 1: 표준 베이지안 갱신
        
        Args:
            invariant: 갱신할 DNAInvariant
            evidence: 새로운 증거
            
        Returns:
            (갱신된 invariant, 갱신 정보)
        """
        prior = self._clip(invariant.confidence)
        alpha = invariant.prior_strength
        
        # 우도 계산
        if evidence.supports_rule:
            likelihood = self.DEFAULT_LIKELIHOOD_SUPPORT * evidence.strength
        else:
            likelihood = self.DEFAULT_LIKELIHOOD_REFUTE + (1 - evidence.strength) * 0.3
        
        # 베이지안 갱신 (prior_strength 적용)
        # P(H|E) = L×P^α / [L×P^α + (1-L)×(1-P)^α]
        numerator = likelihood * (prior ** alpha)
        denominator = numerator + ((1 - likelihood) * ((1 - prior) ** alpha))
        
        # 분모 0 방지
        if denominator < 1e-10:
            posterior = prior
            logger.warning(f"Denominator near zero for {invariant.rule_id}, keeping prior")
        else:
            posterior = numerator / denominator
        
        posterior = self._clip(posterior)
        
        # 갱신 정보 생성
        update = ConfidenceUpdate(
            rule_id=invariant.rule_id,
            prior=invariant.confidence,
            posterior=round(posterior, 4),
            delta=round(posterior - invariant.confidence, 4),
            evidence_count=invariant.evidence_count + 1,
            likelihood=round(likelihood, 4)
        )
        
        # invariant 갱신 (불변 객체이므로 복사)
        updated_invariant = invariant.model_copy(update={
            "confidence": round(posterior, 4),
            "evidence_count": invariant.evidence_count + 1
        })
        
        logger.info(
            f"Bayesian update: {invariant.rule_id} "
            f"{invariant.confidence:.3f} → {posterior:.3f} "
            f"(delta={update.delta:+.3f}, evidence={evidence.evidence_type})"
        )
        
        return updated_invariant, update
    
    def batch_update(
        self,
        invariants: List[DNAInvariant],
        evidences: List[Evidence],
    ) -> Tuple[List[DNAInvariant], List[ConfidenceUpdate]]:
        """
        다중 증거로 일괄 갱신
        
        각 evidence.rule_id에 매칭되는 invariant를 갱신
        
        Returns:
            (갱신된 invariant 리스트, 갱신 정보 리스트)
        """
        invariant_map = {inv.rule_id: inv for inv in invariants}
        updated_invariants = []
        updates = []
        
        for evidence in evidences:
            if evidence.rule_id not in invariant_map:
                logger.warning(f"No invariant found for rule_id={evidence.rule_id}")
                continue
            
            inv = invariant_map[evidence.rule_id]
            updated_inv, update = self.update_confidence(inv, evidence)
            
            # 맵 업데이트 (연속 갱신 지원)
            invariant_map[evidence.rule_id] = updated_inv
            updates.append(update)
        
        updated_invariants = list(invariant_map.values())
        return updated_invariants, updates
    
    def get_low_confidence_rules(
        self,
        invariants: List[DNAInvariant],
        threshold: float = 0.3,
    ) -> List[DNAInvariant]:
        """신뢰도가 낮은 규칙 필터링 (검토 필요)"""
        return [inv for inv in invariants if inv.confidence < threshold]
    
    def get_high_confidence_rules(
        self,
        invariants: List[DNAInvariant],
        threshold: float = 0.8,
    ) -> List[DNAInvariant]:
        """신뢰도가 높은 규칙 필터링 (검증된 규칙)"""
        return [inv for inv in invariants if inv.confidence >= threshold]
    
    def calculate_pack_confidence(
        self,
        invariants: List[DNAInvariant],
    ) -> float:
        """
        Director Pack 전체 신뢰도 계산
        
        가중 평균 (priority 기반)
        """
        if not invariants:
            return 0.5
        
        priority_weights = {
            "critical": 3.0,
            "high": 2.0,
            "medium": 1.0,
            "low": 0.5,
        }
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for inv in invariants:
            weight = priority_weights.get(inv.priority.value, 1.0)
            weighted_sum += inv.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        return round(weighted_sum / total_weight, 4)
    
    def _clip(self, value: float) -> float:
        """값을 안전 범위로 클리핑"""
        return max(self.MIN_CONFIDENCE, min(self.MAX_CONFIDENCE, value))


# 싱글톤 인스턴스
bayesian_engine = BayesianTruthEngine()
