"""
Node Manipulator Service (Hardened)

Intent → VDG 노드 변형 서비스.
DNAInvariant 규칙 검증 + 피드백 루프 연결.

Hardening:
- 입력 검증 강화
- 커스텀 예외
- 속성 타입 검증
- 변경 히스토리
- 상세 로깅
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from app.schemas.intent_schemas import NodeEditIntent, IntentType
from app.schemas.stpf_schemas import STPFInputs
from app.services.stpf_engine import stpf_engine
from app.services.feedback_processor import feedback_processor
from app.schemas.feedback_schemas import ProductionResult, ResultOutcome

logger = logging.getLogger(__name__)


# =========================================================================
# Constants & Configuration
# =========================================================================

# STPF 임계값
STPF_DEATH_VALLEY = 250
STPF_RED_OCEAN = 500
STPF_HIGH_POTENTIAL = 800

# 변경 제한
MAX_CHANGES_PER_REQUEST = 20
MAX_PROPERTY_VALUE_LENGTH = 1000
MAX_BATCH_SIZE = 50
MAX_HISTORY_SIZE = 100

# 허용된 속성 이름 패턴
VALID_PROPERTY_NAME_PATTERN = re.compile(r'^[a-z_][a-z0-9_]{0,49}$')

# 위험한 속성 (변경 불가)
PROTECTED_PROPERTIES: Set[str] = {
    'node_id', 'created_at', 'owner_id', 'is_deleted',
}


# =========================================================================
# Custom Exceptions
# =========================================================================

class NodeManipulatorError(Exception):
    """Node Manipulator 기본 에러"""
    pass


class NodeValidationError(NodeManipulatorError):
    """노드 검증 에러"""
    pass


class PropertyValidationError(NodeManipulatorError):
    """속성 검증 에러"""
    pass


class STFPValidationError(NodeManipulatorError):
    """STPF 검증 실패"""
    pass


class RateLimitError(NodeManipulatorError):
    """변경 빈도 제한"""
    pass


# =========================================================================
# Data Classes
# =========================================================================

@dataclass
class NodeUpdateResult:
    """노드 업데이트 결과"""
    success: bool
    node_id: str
    changes_applied: Dict[str, Any]
    previous_values: Dict[str, Any]
    stpf_score: Optional[float] = None
    stpf_grade: Optional[str] = None
    warnings: List[str] = None
    error: Optional[str] = None
    change_id: Optional[str] = None  # 변경 ID (Undo용)
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.change_id is None and self.success:
            self.change_id = str(uuid4())[:8]


@dataclass
class ChangeHistoryEntry:
    """변경 히스토리 항목"""
    change_id: str
    node_id: str
    changes: Dict[str, Any]
    previous_values: Dict[str, Any]
    timestamp: datetime
    intent_type: IntentType
    stpf_score: float


@dataclass
class VDGNode:
    """VDG 노드 (간소화)"""
    node_id: str
    node_type: str
    properties: Dict[str, Any]
    created_at: datetime = None
    updated_at: datetime = None
    version: int = 1  # 낙관적 락킹용
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


# =========================================================================
# Main Service
# =========================================================================

class NodeManipulator:
    """
    VDG 노드 실시간 변형 (Hardened)
    
    Features:
    - Intent 기반 노드 변형
    - 입력 검증 강화
    - 속성 타입 검증
    - DNAInvariant 규칙 검증
    - STPF 점수 확인
    - 피드백 루프 자동 연결
    - 변경 히스토리 관리
    """
    
    def __init__(self):
        self._change_count = 0
        self._error_count = 0
        self._reject_count = 0
        self._history: List[ChangeHistoryEntry] = []
        logger.info("NodeManipulator initialized (hardened)")
    
    async def apply_intent(
        self,
        intent: NodeEditIntent,
        node: VDGNode,
        validate_rules: bool = True,
        send_feedback: bool = True,
    ) -> NodeUpdateResult:
        """
        Intent를 노드에 적용
        
        Args:
            intent: 적용할 의도
            node: 대상 노드
            validate_rules: DNAInvariant 규칙 검증 여부
            send_feedback: 피드백 루프에 기록 여부
        
        Returns:
            NodeUpdateResult
        
        Raises:
            NodeValidationError: 노드 검증 실패
            PropertyValidationError: 속성 검증 실패
        """
        self._change_count += 1
        
        try:
            # 1. 노드 검증
            self._validate_node(node)
            
            # 2. 변경 사항 추출 및 검증
            raw_changes = intent.to_simple_dict()
            changes = self._validate_and_sanitize_changes(raw_changes)
            
            if not changes:
                return NodeUpdateResult(
                    success=False,
                    node_id=node.node_id,
                    changes_applied={},
                    previous_values={},
                    error="유효한 변경 사항이 없습니다",
                )
            
            # 3. 보호된 속성 확인
            protected = set(changes.keys()) & PROTECTED_PROPERTIES
            if protected:
                logger.warning(f"Protected properties blocked: {protected}")
                return NodeUpdateResult(
                    success=False,
                    node_id=node.node_id,
                    changes_applied={},
                    previous_values={},
                    error=f"보호된 속성은 변경할 수 없습니다: {protected}",
                )
            
            # 4. STPF 평가
            stpf_result = self._evaluate_change(node, changes, intent.intent_type)
            stpf_score = stpf_result.score_1000
            stpf_grade = stpf_result.grade
            
            warnings = []
            
            # 5. STPF 점수 검증
            if stpf_score < STPF_DEATH_VALLEY:
                self._reject_count += 1
                logger.warning(
                    f"STPF Death Valley rejected: node={node.node_id}, "
                    f"score={stpf_score}, changes={len(changes)}"
                )
                return NodeUpdateResult(
                    success=False,
                    node_id=node.node_id,
                    changes_applied={},
                    previous_values={},
                    stpf_score=stpf_score,
                    stpf_grade=stpf_grade,
                    error=f"변경이 거부되었습니다 (STPF {stpf_score:.0f} < {STPF_DEATH_VALLEY})",
                )
            
            if stpf_score < STPF_RED_OCEAN:
                warnings.append(f"STPF 점수 주의: {stpf_score:.0f} (Red Ocean)")
            elif stpf_score < STPF_HIGH_POTENTIAL:
                warnings.append(f"STPF High Potential: {stpf_score:.0f}")
            
            # 6. DNAInvariant 규칙 검증
            if validate_rules:
                rule_violations = self._validate_dna_rules(node, changes)
                if rule_violations:
                    for v in rule_violations:
                        warnings.append(f"규칙 위반: {v}")
            
            # 7. 이전 값 저장
            previous_values = {}
            for key in changes:
                if key in node.properties:
                    previous_values[key] = self._deep_copy_value(node.properties[key])
            
            # 8. 변경 적용
            for key, value in changes.items():
                node.properties[key] = value
            node.updated_at = datetime.utcnow()
            node.version += 1
            
            # 9. 히스토리 기록
            change_id = str(uuid4())[:8]
            self._add_to_history(ChangeHistoryEntry(
                change_id=change_id,
                node_id=node.node_id,
                changes=changes,
                previous_values=previous_values,
                timestamp=datetime.utcnow(),
                intent_type=intent.intent_type,
                stpf_score=stpf_score,
            ))
            
            logger.info(
                f"Node updated: node={node.node_id}, "
                f"change_id={change_id}, "
                f"changes={len(changes)}, "
                f"stpf={stpf_score:.0f}, "
                f"version={node.version}"
            )
            
            # 10. 피드백 루프에 기록
            if send_feedback:
                await self._send_feedback(
                    node_id=node.node_id,
                    intent=intent,
                    success=True,
                    stpf_score=stpf_score,
                )
            
            return NodeUpdateResult(
                success=True,
                node_id=node.node_id,
                changes_applied=changes,
                previous_values=previous_values,
                stpf_score=stpf_score,
                stpf_grade=stpf_grade,
                warnings=warnings,
                change_id=change_id,
            )
            
        except NodeManipulatorError as e:
            self._error_count += 1
            logger.warning(f"Validation error: {e}")
            return NodeUpdateResult(
                success=False,
                node_id=node.node_id if node else "unknown",
                changes_applied={},
                previous_values={},
                error=str(e),
            )
        except Exception as e:
            self._error_count += 1
            logger.error(f"Node manipulation error: {e}", exc_info=True)
            return NodeUpdateResult(
                success=False,
                node_id=node.node_id if node else "unknown",
                changes_applied={},
                previous_values={},
                error=f"내부 오류: {str(e)[:100]}",
            )
    
    def _validate_node(self, node: VDGNode) -> None:
        """노드 검증"""
        if not node:
            raise NodeValidationError("노드가 None입니다")
        
        if not node.node_id:
            raise NodeValidationError("노드 ID가 없습니다")
        
        if not node.node_type:
            raise NodeValidationError("노드 타입이 없습니다")
        
        if node.properties is None:
            node.properties = {}
    
    def _validate_and_sanitize_changes(
        self,
        raw_changes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """변경 검증 및 정규화"""
        if not raw_changes:
            raise PropertyValidationError("변경 사항이 비어있습니다")
        
        # 변경 수 제한
        if len(raw_changes) > MAX_CHANGES_PER_REQUEST:
            logger.warning(f"Truncating changes: {len(raw_changes)} -> {MAX_CHANGES_PER_REQUEST}")
            raw_changes = dict(list(raw_changes.items())[:MAX_CHANGES_PER_REQUEST])
        
        validated = {}
        
        for key, value in raw_changes.items():
            # 속성 이름 검증
            if not isinstance(key, str):
                continue
            
            # 속성 이름 정규화 (소문자 + 언더스코어)
            normalized_key = key.lower().replace('-', '_').replace(' ', '_')
            
            # 값 검증 및 정규화
            validated_value = self._validate_property_value(normalized_key, value)
            if validated_value is not None:
                validated[normalized_key] = validated_value
        
        return validated
    
    def _validate_property_value(
        self,
        key: str,
        value: Any,
    ) -> Optional[Any]:
        """속성 값 검증"""
        # None 허용
        if value is None:
            return None
        
        # 문자열 길이 제한
        if isinstance(value, str):
            if len(value) > MAX_PROPERTY_VALUE_LENGTH:
                logger.warning(f"Truncating string value for {key}")
                return value[:MAX_PROPERTY_VALUE_LENGTH]
            # 위험한 문자 제거
            return re.sub(r'[<>\'";]', '', value)
        
        # 숫자 범위 검증 (0-100 스케일 가정)
        if isinstance(value, (int, float)):
            if value < 0:
                return 0
            if value > 100:
                return 100
            return value
        
        # 리스트 크기 제한
        if isinstance(value, list):
            if len(value) > 50:
                return value[:50]
            return value
        
        # 딕셔너리 (중첩 제한)
        if isinstance(value, dict):
            if len(value) > 20:
                return dict(list(value.items())[:20])
            return value
        
        # 기타 타입
        return value
    
    def _deep_copy_value(self, value: Any) -> Any:
        """값 깊은 복사"""
        if isinstance(value, dict):
            return {k: self._deep_copy_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._deep_copy_value(v) for v in value]
        return value
    
    async def batch_apply(
        self,
        intent: NodeEditIntent,
        nodes: List[VDGNode],
    ) -> List[NodeUpdateResult]:
        """다중 노드에 Intent 적용"""
        # 배치 크기 제한
        if len(nodes) > MAX_BATCH_SIZE:
            logger.warning(f"Batch size limited: {len(nodes)} -> {MAX_BATCH_SIZE}")
            nodes = nodes[:MAX_BATCH_SIZE]
        
        results = []
        
        for node in nodes:
            result = await self.apply_intent(intent, node, send_feedback=False)
            results.append(result)
        
        # 배치 결과 피드백
        success_count = sum(1 for r in results if r.success)
        await self._send_batch_feedback(intent, success_count, len(nodes))
        
        logger.info(
            f"Batch apply complete: success={success_count}/{len(nodes)}"
        )
        
        return results
    
    def preview_changes(
        self,
        intent: NodeEditIntent,
        node: VDGNode,
    ) -> Dict[str, Any]:
        """변경 미리보기"""
        try:
            self._validate_node(node)
            changes = self._validate_and_sanitize_changes(intent.to_simple_dict())
        except NodeManipulatorError as e:
            return {
                "node_id": node.node_id if node else "unknown",
                "error": str(e),
                "changes": [],
                "recommended": False,
            }
        
        preview = {
            "node_id": node.node_id,
            "changes": [],
            "protected_blocked": [],
        }
        
        for key, new_value in changes.items():
            if key in PROTECTED_PROPERTIES:
                preview["protected_blocked"].append(key)
                continue
            
            old_value = node.properties.get(key, None)
            preview["changes"].append({
                "property": key,
                "old_value": old_value,
                "new_value": new_value,
                "is_new": old_value is None,
            })
        
        # STPF 평가
        if preview["changes"]:
            stpf_result = self._evaluate_change(node, changes, intent.intent_type)
            preview["stpf_score"] = stpf_result.score_1000
            preview["stpf_grade"] = stpf_result.grade
            preview["recommended"] = stpf_result.score_1000 >= STPF_RED_OCEAN
        else:
            preview["stpf_score"] = 0
            preview["recommended"] = False
        
        return preview
    
    def undo_by_change_id(
        self,
        node: VDGNode,
        change_id: str,
    ) -> NodeUpdateResult:
        """변경 ID로 Undo"""
        # 히스토리에서 찾기
        entry = next(
            (h for h in reversed(self._history) if h.change_id == change_id and h.node_id == node.node_id),
            None
        )
        
        if not entry:
            return NodeUpdateResult(
                success=False,
                node_id=node.node_id,
                changes_applied={},
                previous_values={},
                error=f"변경 ID를 찾을 수 없습니다: {change_id}",
            )
        
        return self.undo_change(node, entry.previous_values)
    
    def undo_change(
        self,
        node: VDGNode,
        previous_values: Dict[str, Any],
    ) -> NodeUpdateResult:
        """변경 취소 (Undo)"""
        if not previous_values:
            return NodeUpdateResult(
                success=False,
                node_id=node.node_id,
                changes_applied={},
                previous_values={},
                error="되돌릴 변경이 없습니다",
            )
        
        changes_reverted = {}
        
        for key, old_value in previous_values.items():
            if old_value is None:
                if key in node.properties:
                    del node.properties[key]
                    changes_reverted[key] = "removed"
            else:
                node.properties[key] = old_value
                changes_reverted[key] = old_value
        
        node.updated_at = datetime.utcnow()
        node.version += 1
        
        logger.info(
            f"Node reverted: node={node.node_id}, "
            f"keys={list(previous_values.keys())}, "
            f"version={node.version}"
        )
        
        return NodeUpdateResult(
            success=True,
            node_id=node.node_id,
            changes_applied=changes_reverted,
            previous_values={},
        )
    
    def _evaluate_change(
        self,
        node: VDGNode,
        changes: Dict[str, Any],
        intent_type: IntentType = IntentType.MODIFY,
    ):
        """변경에 대한 STPF 평가"""
        num_changes = len(changes)
        
        # 의도 유형별 리스크 조정
        risk_modifier = 0
        if intent_type == IntentType.DELETE:
            risk_modifier = 3
        elif intent_type == IntentType.BATCH_EDIT:
            risk_modifier = 2
        elif intent_type == IntentType.CREATE:
            risk_modifier = 1
        
        inputs = STPFInputs(
            Trust=8.0,
            Legality=10.0,
            Hygiene=8.0,
            E=7.0,
            K=7.0,
            Nv=5.0,
            Cn=8.0,
            Prf=5.0,
            Cost=min(10.0, 3.0 + num_changes * 0.3),
            Risk=min(10.0, 3.0 + risk_modifier),
            Threat=2.0,
            Pressure=3.0,
            Lag=2.0,
            Uncertainty=4.0,
            Network=5.0,
            Scarcity=5.0,
            Leverage=6.0,
            Expectation=6.0,
            Reality=7.0,
        )
        
        return stpf_engine.compute(inputs)
    
    def _validate_dna_rules(
        self,
        node: VDGNode,
        changes: Dict[str, Any],
    ) -> List[str]:
        """DNAInvariant 규칙 검증"""
        violations = []
        
        try:
            rules = feedback_processor.get_all_rules()
            
            for rule in rules:
                if rule.condition in changes:
                    new_value = changes[rule.condition]
                    
                    if hasattr(rule, 'spec') and rule.spec:
                        spec = rule.spec
                        try:
                            if spec.operator == "gte" and float(new_value) < float(spec.value):
                                violations.append(f"{rule.name}: {rule.condition} >= {spec.value}")
                            elif spec.operator == "lte" and float(new_value) > float(spec.value):
                                violations.append(f"{rule.name}: {rule.condition} <= {spec.value}")
                        except (ValueError, TypeError):
                            pass
        except Exception as e:
            logger.warning(f"DNA rule validation error: {e}")
        
        return violations
    
    def _add_to_history(self, entry: ChangeHistoryEntry) -> None:
        """히스토리 추가 (제한 적용)"""
        self._history.append(entry)
        
        # 최대 크기 유지
        if len(self._history) > MAX_HISTORY_SIZE:
            self._history = self._history[-MAX_HISTORY_SIZE:]
    
    def get_history(
        self,
        node_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """변경 히스토리 조회"""
        history = self._history
        
        if node_id:
            history = [h for h in history if h.node_id == node_id]
        
        return [
            {
                "change_id": h.change_id,
                "node_id": h.node_id,
                "timestamp": h.timestamp.isoformat(),
                "intent_type": h.intent_type.value,
                "stpf_score": h.stpf_score,
                "change_count": len(h.changes),
            }
            for h in list(reversed(history))[:limit]
        ]
    
    async def _send_feedback(
        self,
        node_id: str,
        intent: NodeEditIntent,
        success: bool,
        stpf_score: float,
    ):
        """피드백 루프에 결과 기록"""
        try:
            result = ProductionResult(
                capsule_id=f"node_edit_{node_id}",
                result_id=str(uuid4())[:8],
                outcome=ResultOutcome.SUCCESS if success else ResultOutcome.FAILURE,
                score=min(10.0, stpf_score / 100),
                rule_ids=[],
                meta={
                    "intent_type": intent.intent_type.value,
                    "change_count": len(intent.to_simple_dict()),
                },
            )
            
            feedback_processor.process_production_result(result)
            logger.debug(f"Feedback sent: node={node_id}, score={stpf_score}")
            
        except Exception as e:
            logger.warning(f"Failed to send feedback: {e}")
    
    async def _send_batch_feedback(
        self,
        intent: NodeEditIntent,
        success_count: int,
        total_count: int,
    ):
        """배치 작업 피드백"""
        try:
            result = ProductionResult(
                capsule_id=f"batch_edit_{intent.intent_id}",
                result_id=str(uuid4())[:8],
                outcome=ResultOutcome.SUCCESS if success_count == total_count else ResultOutcome.PARTIAL,
                score=min(10.0, success_count / max(1, total_count) * 10),
                rule_ids=[],
                meta={
                    "success_count": success_count,
                    "total_count": total_count,
                    "success_rate": success_count / max(1, total_count),
                },
            )
            
            feedback_processor.process_production_result(result)
            
        except Exception as e:
            logger.warning(f"Failed to send batch feedback: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """통계"""
        return {
            "total_changes": self._change_count,
            "error_count": self._error_count,
            "reject_count": self._reject_count,
            "error_rate": self._error_count / max(1, self._change_count),
            "reject_rate": self._reject_count / max(1, self._change_count),
            "history_size": len(self._history),
        }


# 싱글톤 인스턴스
node_manipulator = NodeManipulator()
