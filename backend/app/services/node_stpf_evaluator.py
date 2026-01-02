"""
Node STPF Evaluator

노드 변경에 대한 STPF 깊은 통합.
변경 유형별 리스크 평가 + Grade별 자동 행동.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.schemas.stpf_schemas import STPFInputs, STPFResult
from app.schemas.intent_schemas import NodeEditIntent, IntentType
from app.services.stpf_engine import stpf_engine
from app.services.kelly_allocator import kelly_allocator

logger = logging.getLogger(__name__)


# =========================================================================
# Constants
# =========================================================================

# STPF Grade 임계값
GRADE_UNICORN = 800
GRADE_HIGH_POTENTIAL = 500
GRADE_RED_OCEAN = 250

# Grade별 행동
class GradeAction(str, Enum):
    """Grade별 자동 행동"""
    AUTO_APPLY = "auto_apply"           # 즉시 적용
    APPLY_WITH_LOG = "apply_with_log"   # 적용 + 상세 로깅
    CONFIRM_REQUIRED = "confirm_required"  # 사용자 확인 필요
    REJECT = "reject"                   # 거부
    SUGGEST_ALTERNATIVE = "suggest_alternative"  # 대안 제시


# 변경 유형별 리스크 가중치
INTENT_TYPE_RISK = {
    IntentType.MODIFY: 0,
    IntentType.CREATE: 1,
    IntentType.DELETE: 5,
    IntentType.CONNECT: 1,
    IntentType.BATCH_EDIT: 3,
    IntentType.PREVIEW: 0,
    IntentType.UNDO: 0,
}

# 속성별 리스크 가중치
PROPERTY_RISK = {
    # 높은 리스크 (시각적 변화 큼)
    "mood": 2,
    "color_grade": 2,
    "lighting": 2,
    "contrast": 1,
    
    # 중간 리스크
    "camera_motion": 1,
    "speed": 1,
    "pacing": 1,
    
    # 낮은 리스크
    "description": 0,
    "name": 0,
    "tags": 0,
}


# =========================================================================
# Data Classes
# =========================================================================

@dataclass
class NodeEvaluation:
    """노드 변경 평가 결과"""
    # STPF 결과
    stpf_result: STPFResult
    score: float
    grade: str
    
    # 행동 권장
    action: GradeAction
    action_reason: str
    
    # Kelly 권장
    kelly_fraction: Optional[float] = None
    kelly_recommendation: Optional[str] = None
    
    # 리스크 분석
    total_risk: float = 0.0
    risk_breakdown: Dict[str, float] = None
    
    # 메타
    evaluated_at: datetime = None
    
    def __post_init__(self):
        if self.evaluated_at is None:
            self.evaluated_at = datetime.utcnow()
        if self.risk_breakdown is None:
            self.risk_breakdown = {}


@dataclass 
class AlternativeSuggestion:
    """대안 제안"""
    original_change: Dict[str, Any]
    suggested_change: Dict[str, Any]
    reason: str
    expected_score_delta: float


# =========================================================================
# Main Service
# =========================================================================

class NodeSTPFEvaluator:
    """
    노드 변경 STPF 평가기
    
    Features:
    - 변경 유형별 리스크 평가
    - 속성별 리스크 가중치
    - Grade별 자동 행동 결정
    - Kelly 통합
    - 대안 제안
    """
    
    def __init__(self):
        self._eval_count = 0
        self._reject_count = 0
        logger.info("NodeSTPFEvaluator initialized")
    
    def evaluate_intent(
        self,
        intent: NodeEditIntent,
        current_properties: Optional[Dict[str, Any]] = None,
    ) -> NodeEvaluation:
        """
        Intent 평가
        
        Args:
            intent: 평가할 의도
            current_properties: 현재 노드 속성
            
        Returns:
            NodeEvaluation with STPF score and action
        """
        self._eval_count += 1
        
        # 1. 리스크 분석
        risk_breakdown, total_risk = self._analyze_risk(intent)
        
        # 2. STPF 입력 생성
        stpf_inputs = self._build_stpf_inputs(intent, total_risk, current_properties)
        
        # 3. STPF 계산
        stpf_result = stpf_engine.compute(stpf_inputs)
        score = stpf_result.score_1000
        grade = stpf_result.grade
        
        # 4. 행동 결정
        action, action_reason = self._determine_action(score, grade, intent)
        
        if action == GradeAction.REJECT:
            self._reject_count += 1
        
        # 5. Kelly 계산
        kelly_fraction = None
        kelly_recommendation = None
        
        if stpf_result.p_success > 0:
            try:
                kelly_result = kelly_allocator.calculate_allocation(
                    user_balance=1000,
                    base_cost=10,
                    success_probability=min(0.95, max(0.05, stpf_result.p_success)),
                    reward_ratio=2.0,
                )
                kelly_fraction = kelly_result.kelly.f_safe
                kelly_recommendation = kelly_result.kelly.recommendation
            except Exception as e:
                logger.warning(f"Kelly calculation failed: {e}")
        
        logger.info(
            f"Node evaluation: score={score:.0f}, grade={grade}, "
            f"action={action.value}, risk={total_risk:.1f}"
        )
        
        return NodeEvaluation(
            stpf_result=stpf_result,
            score=score,
            grade=grade,
            action=action,
            action_reason=action_reason,
            kelly_fraction=kelly_fraction,
            kelly_recommendation=kelly_recommendation,
            total_risk=total_risk,
            risk_breakdown=risk_breakdown,
        )
    
    def evaluate_changes(
        self,
        changes: Dict[str, Any],
        intent_type: IntentType = IntentType.MODIFY,
    ) -> NodeEvaluation:
        """변경 사항 직접 평가"""
        intent = NodeEditIntent(
            intent_type=intent_type,
            original_text="direct evaluation",
            simple_changes=changes,
        )
        return self.evaluate_intent(intent)
    
    def suggest_alternatives(
        self,
        intent: NodeEditIntent,
        current_eval: NodeEvaluation,
    ) -> List[AlternativeSuggestion]:
        """
        변경이 거부된 경우 대안 제안
        """
        if current_eval.action not in [GradeAction.REJECT, GradeAction.SUGGEST_ALTERNATIVE]:
            return []
        
        suggestions = []
        changes = intent.to_simple_dict()
        
        for key, value in changes.items():
            risk = PROPERTY_RISK.get(key, 1)
            
            if risk >= 2:
                # 높은 리스크 속성은 더 온건한 값 제안
                if isinstance(value, (int, float)):
                    # 숫자면 절반으로
                    moderate_value = value * 0.5 if value > 5 else value + 1
                    suggestions.append(AlternativeSuggestion(
                        original_change={key: value},
                        suggested_change={key: moderate_value},
                        reason=f"{key}를 더 온건하게 조정",
                        expected_score_delta=50,
                    ))
                elif isinstance(value, str) and value in ["dramatic", "extreme"]:
                    # 극단적인 문자열 값 완화
                    moderate_map = {"dramatic": "moderate", "extreme": "normal"}
                    suggestions.append(AlternativeSuggestion(
                        original_change={key: value},
                        suggested_change={key: moderate_map.get(value, value)},
                        reason=f"{key}를 더 중립적으로",
                        expected_score_delta=30,
                    ))
        
        return suggestions
    
    def batch_evaluate(
        self,
        intents: List[NodeEditIntent],
    ) -> List[NodeEvaluation]:
        """배치 평가"""
        return [self.evaluate_intent(intent) for intent in intents]
    
    def _analyze_risk(
        self,
        intent: NodeEditIntent,
    ) -> tuple[Dict[str, float], float]:
        """리스크 분석"""
        risk_breakdown = {}
        
        # 1. 의도 유형 리스크
        type_risk = INTENT_TYPE_RISK.get(intent.intent_type, 1)
        risk_breakdown["intent_type"] = type_risk
        
        # 2. 속성별 리스크
        changes = intent.to_simple_dict()
        property_risk = 0.0
        
        for key, value in changes.items():
            prop_risk = PROPERTY_RISK.get(key, 1)
            risk_breakdown[f"prop_{key}"] = prop_risk
            property_risk += prop_risk
            
            # 값의 극단성 체크
            if isinstance(value, (int, float)):
                if value <= 1 or value >= 9:
                    risk_breakdown[f"extreme_{key}"] = 1
                    property_risk += 1
        
        risk_breakdown["properties"] = property_risk
        
        # 3. 변경 수 리스크
        change_count_risk = min(5, len(changes) * 0.5)
        risk_breakdown["change_count"] = change_count_risk
        
        # 4. 신뢰도 리스크 (낮은 신뢰도 = 높은 리스크)
        confidence_risk = max(0, (1 - intent.overall_confidence) * 3)
        risk_breakdown["confidence"] = confidence_risk
        
        total_risk = type_risk + property_risk + change_count_risk + confidence_risk
        
        return risk_breakdown, total_risk
    
    def _build_stpf_inputs(
        self,
        intent: NodeEditIntent,
        total_risk: float,
        current_properties: Optional[Dict[str, Any]] = None,
    ) -> STPFInputs:
        """STPF 입력 생성"""
        num_changes = len(intent.to_simple_dict())
        
        # 동적 값 계산
        essence = min(10, 6 + intent.overall_confidence * 2)
        risk_score = min(10, 3 + total_risk * 0.5)
        
        return STPFInputs(
            # Gates
            Trust=8.0,
            Legality=10.0,
            Hygiene=8.0,
            
            # Numerator
            E=essence,
            K=7.0,
            Nv=5.0,
            Cn=8.0,  # 사용자 직접 요청
            Prf=5.0,
            
            # Denominator (리스크 기반)
            Cost=min(10.0, 3.0 + num_changes * 0.4),
            Risk=risk_score,
            Threat=2.0,
            Pressure=3.0,
            Lag=2.0,
            Uncertainty=min(10.0, 4.0 + (1 - intent.overall_confidence) * 3),
            
            # Multipliers
            Network=5.0,
            Scarcity=5.0,
            Leverage=6.0,
            
            # Context
            Expectation=6.0,
            Reality=7.0,
        )
    
    def _determine_action(
        self,
        score: float,
        grade: str,
        intent: NodeEditIntent,
    ) -> tuple[GradeAction, str]:
        """행동 결정"""
        # Unicorn: 자동 적용
        if score >= GRADE_UNICORN:
            return GradeAction.AUTO_APPLY, f"Unicorn 등급 ({score:.0f}점) - 자동 적용"
        
        # High Potential: 로깅 후 적용
        if score >= GRADE_HIGH_POTENTIAL:
            return GradeAction.APPLY_WITH_LOG, f"High Potential ({score:.0f}점) - 적용 및 로깅"
        
        # Red Ocean: 확인 필요
        if score >= GRADE_RED_OCEAN:
            return GradeAction.CONFIRM_REQUIRED, f"Red Ocean ({score:.0f}점) - 사용자 확인 필요"
        
        # Death Valley: 거부
        if intent.intent_type == IntentType.DELETE:
            return GradeAction.REJECT, f"위험한 삭제 작업 ({score:.0f}점)"
        
        return GradeAction.SUGGEST_ALTERNATIVE, f"Death Valley ({score:.0f}점) - 대안 제시"
    
    def get_grade_thresholds(self) -> Dict[str, int]:
        """Grade 임계값 조회"""
        return {
            "unicorn": GRADE_UNICORN,
            "high_potential": GRADE_HIGH_POTENTIAL,
            "red_ocean": GRADE_RED_OCEAN,
            "death_valley": 0,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계"""
        return {
            "total_evaluations": self._eval_count,
            "reject_count": self._reject_count,
            "reject_rate": self._reject_count / max(1, self._eval_count),
        }


# 싱글톤 인스턴스
node_stpf_evaluator = NodeSTPFEvaluator()
