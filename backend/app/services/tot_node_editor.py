"""
ToT Node Editor

복잡한 다중 노드 편집을 위한 Tree of Thoughts 통합.
MCTS로 최적 편집 경로 탐색.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.schemas.tot_schemas import (
    ThoughtNode, SearchStrategy, SimulationRequest, SimulationResult,
)
from app.schemas.intent_schemas import NodeEditIntent, IntentType, COMPLEX_PATTERNS
from app.services.tot_simulator import tot_simulator
from app.services.intent_parser import intent_parser
from app.services.node_stpf_evaluator import node_stpf_evaluator, GradeAction
from app.services.node_manipulator import node_manipulator, VDGNode

logger = logging.getLogger(__name__)


# =========================================================================
# Constants
# =========================================================================

# 복잡 편집 임계값
MIN_NODES_FOR_TOT = 3
MIN_CHANGES_FOR_TOT = 5

# ToT 기본 설정
DEFAULT_MAX_DEPTH = 3
DEFAULT_BRANCHING_FACTOR = 3
DEFAULT_MAX_ITERATIONS = 50


# =========================================================================
# Data Classes
# =========================================================================

@dataclass
class EditStep:
    """편집 단계"""
    step_id: str
    node_id: str
    changes: Dict[str, Any]
    description: str
    stpf_score: Optional[float] = None
    applied: bool = False


@dataclass
class EditPlan:
    """편집 계획"""
    plan_id: str
    user_request: str
    steps: List[EditStep]
    total_stpf_score: float = 0.0
    estimated_risk: float = 0.0
    recommendation: str = ""
    alternatives: List[List[EditStep]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TotEditResult:
    """ToT 편집 결과"""
    success: bool
    plan: Optional[EditPlan] = None
    applied_steps: List[EditStep] = field(default_factory=list)
    skipped_steps: List[EditStep] = field(default_factory=list)
    total_applied: int = 0
    total_skipped: int = 0
    error: Optional[str] = None


# =========================================================================
# Main Service
# =========================================================================

class ToTNodeEditor:
    """
    ToT 기반 복잡 노드 편집기
    
    Features:
    - 복잡한 편집 요청 감지
    - MCTS로 최적 편집 경로 탐색
    - 다중 노드 편집 계획 수립
    - 단계별 실행 및 롤백
    """
    
    def __init__(self):
        self._plan_count = 0
        self._exec_count = 0
        logger.info("ToTNodeEditor initialized")
    
    def is_complex_edit(
        self,
        user_input: str,
        node_count: int = 1,
        change_count: int = 1,
    ) -> tuple[bool, str]:
        """
        복잡한 편집인지 판단
        
        Returns:
            (is_complex, reason)
        """
        # 패턴 매칭
        import re
        for pattern in COMPLEX_PATTERNS:
            if re.search(pattern.pattern, user_input):
                return True, pattern.description
        
        # 노드 수 기반
        if node_count >= MIN_NODES_FOR_TOT:
            return True, f"다중 노드 편집 ({node_count}개)"
        
        # 변경 수 기반
        if change_count >= MIN_CHANGES_FOR_TOT:
            return True, f"다수 변경 ({change_count}개)"
        
        # 키워드 기반
        complex_keywords = ["전체", "모든", "모두", "처음부터", "끝까지", "일괄"]
        for kw in complex_keywords:
            if kw in user_input:
                return True, f"키워드 '{kw}' 감지"
        
        return False, "단순 편집"
    
    def plan_edit(
        self,
        user_request: str,
        nodes: List[VDGNode],
        strategy: SearchStrategy = SearchStrategy.MCTS,
    ) -> EditPlan:
        """
        복잡한 편집 계획 수립 (ToT 사용)
        
        Args:
            user_request: 사용자 요청
            nodes: 대상 노드들
            strategy: 탐색 전략
            
        Returns:
            EditPlan with steps
        """
        self._plan_count += 1
        plan_id = str(uuid4())[:8]
        
        logger.info(f"Planning edit: request='{user_request[:50]}...', nodes={len(nodes)}")
        
        # 1. Intent 파싱
        from app.schemas.intent_schemas import IntentParseRequest
        parse_result = intent_parser.parse(IntentParseRequest(
            user_input=user_request,
            include_stpf_eval=True,
        ))
        
        if not parse_result.success:
            return EditPlan(
                plan_id=plan_id,
                user_request=user_request,
                steps=[],
                recommendation=f"의도 파싱 실패: {parse_result.error}",
            )
        
        base_changes = parse_result.intent.to_simple_dict()
        
        # 2. ToT 시뮬레이션
        tot_request = SimulationRequest(
            problem=f"'{user_request}'을 {len(nodes)}개 노드에 적용하는 최적 전략",
            strategy=strategy,
            max_depth=DEFAULT_MAX_DEPTH,
            branching_factor=DEFAULT_BRANCHING_FACTOR,
            max_iterations=DEFAULT_MAX_ITERATIONS,
            context={
                "node_count": len(nodes),
                "base_changes": base_changes,
            },
        )
        
        tot_result = tot_simulator.simulate(
            tot_request,
            thought_generator=self._edit_thought_generator,
        )
        
        # 3. 경로를 편집 단계로 변환
        steps = self._path_to_steps(tot_result.best_path, nodes, base_changes)
        
        # 4. 각 단계 STPF 평가
        total_score = 0.0
        total_risk = 0.0
        
        for step in steps:
            eval_result = node_stpf_evaluator.evaluate_changes(
                step.changes,
                IntentType.MODIFY,
            )
            step.stpf_score = eval_result.score
            total_score += eval_result.score
            total_risk += eval_result.total_risk
        
        avg_score = total_score / len(steps) if steps else 0
        
        # 5. 대안 경로
        alternatives = []
        for alt_path in tot_result.alternative_paths[:2]:
            alt_steps = self._thoughts_to_steps(alt_path, nodes, base_changes)
            alternatives.append(alt_steps)
        
        plan = EditPlan(
            plan_id=plan_id,
            user_request=user_request,
            steps=steps,
            total_stpf_score=avg_score,
            estimated_risk=total_risk / len(steps) if steps else 0,
            recommendation=tot_result.recommendation,
            alternatives=alternatives,
        )
        
        logger.info(
            f"Edit plan created: id={plan_id}, steps={len(steps)}, "
            f"avg_score={avg_score:.0f}"
        )
        
        return plan
    
    async def execute_plan(
        self,
        plan: EditPlan,
        nodes: Dict[str, VDGNode],
        skip_low_score: bool = True,
        min_score: float = 250,
    ) -> TotEditResult:
        """
        편집 계획 실행
        
        Args:
            plan: 실행할 계획
            nodes: 노드 ID -> VDGNode 매핑
            skip_low_score: 낮은 점수 단계 건너뛰기
            min_score: 최소 점수
            
        Returns:
            TotEditResult
        """
        self._exec_count += 1
        applied_steps = []
        skipped_steps = []
        
        logger.info(f"Executing plan: {plan.plan_id}, steps={len(plan.steps)}")
        
        for step in plan.steps:
            # 점수 확인
            if skip_low_score and step.stpf_score and step.stpf_score < min_score:
                logger.info(f"Skipping low-score step: {step.step_id}, score={step.stpf_score}")
                skipped_steps.append(step)
                continue
            
            # 노드 조회
            node = nodes.get(step.node_id)
            if not node:
                logger.warning(f"Node not found: {step.node_id}")
                skipped_steps.append(step)
                continue
            
            # Intent 생성
            intent = NodeEditIntent(
                intent_type=IntentType.MODIFY,
                target_node_id=step.node_id,
                original_text=step.description,
                simple_changes=step.changes,
            )
            
            # 적용
            result = await node_manipulator.apply_intent(intent, node)
            
            if result.success:
                step.applied = True
                applied_steps.append(step)
            else:
                skipped_steps.append(step)
        
        logger.info(
            f"Plan executed: applied={len(applied_steps)}, "
            f"skipped={len(skipped_steps)}"
        )
        
        return TotEditResult(
            success=len(applied_steps) > 0,
            plan=plan,
            applied_steps=applied_steps,
            skipped_steps=skipped_steps,
            total_applied=len(applied_steps),
            total_skipped=len(skipped_steps),
        )
    
    def quick_plan(
        self,
        user_request: str,
        node_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        빠른 계획 (ToT 없이)
        """
        from app.schemas.intent_schemas import IntentParseRequest
        parse_result = intent_parser.parse(IntentParseRequest(
            user_input=user_request,
            include_stpf_eval=False,
        ))
        
        if not parse_result.success:
            return []
        
        changes = parse_result.intent.to_simple_dict()
        
        return [
            {
                "node_id": nid,
                "changes": changes,
                "description": user_request,
            }
            for nid in node_ids
        ]
    
    def _edit_thought_generator(
        self,
        parent_thought: str,
        problem: str,
    ) -> List[str]:
        """편집 특화 생각 생성기"""
        strategies = [
            f"점진적 변경: 한 속성씩 순차적으로",
            f"일괄 변경: 모든 노드에 동시 적용",
            f"우선순위 변경: 중요 노드부터 적용",
            f"안전한 변경: 리스크 낮은 속성 먼저",
            f"대담한 변경: 핵심 속성부터 바로",
        ]
        return strategies[:3]  # 3개만
    
    def _path_to_steps(
        self,
        path: List[ThoughtNode],
        nodes: List[VDGNode],
        base_changes: Dict[str, Any],
    ) -> List[EditStep]:
        """경로를 편집 단계로 변환"""
        steps = []
        
        # 전략에 따라 단계 생성
        strategy = path[-1].thought if path else "일괄 변경"
        
        if "점진적" in strategy:
            # 속성별로 순차 적용
            for key, value in base_changes.items():
                for node in nodes:
                    steps.append(EditStep(
                        step_id=str(uuid4())[:8],
                        node_id=node.node_id,
                        changes={key: value},
                        description=f"{node.node_id}의 {key}를 {value}로",
                    ))
        elif "우선순위" in strategy:
            # 첫 번째 노드에 모든 변경, 그 다음 노드들
            for node in nodes:
                steps.append(EditStep(
                    step_id=str(uuid4())[:8],
                    node_id=node.node_id,
                    changes=base_changes,
                    description=f"{node.node_id}에 변경 적용",
                ))
        else:
            # 기본: 일괄 변경
            for node in nodes:
                steps.append(EditStep(
                    step_id=str(uuid4())[:8],
                    node_id=node.node_id,
                    changes=base_changes,
                    description=f"{node.node_id}에 변경 적용",
                ))
        
        return steps
    
    def _thoughts_to_steps(
        self,
        thoughts: List[str],
        nodes: List[VDGNode],
        base_changes: Dict[str, Any],
    ) -> List[EditStep]:
        """생각 목록을 단계로 변환"""
        steps = []
        for i, node in enumerate(nodes):
            desc = thoughts[i] if i < len(thoughts) else f"Step {i+1}"
            steps.append(EditStep(
                step_id=str(uuid4())[:8],
                node_id=node.node_id,
                changes=base_changes,
                description=desc,
            ))
        return steps
    
    def get_stats(self) -> Dict[str, Any]:
        """통계"""
        return {
            "total_plans": self._plan_count,
            "total_executions": self._exec_count,
        }


# 싱글톤 인스턴스
tot_node_editor = ToTNodeEditor()
