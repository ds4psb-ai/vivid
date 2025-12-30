"""
Arc Compliance Validator

Validates narrative structure compliance for shot contracts.
Works alongside DNA validator to ensure both story and style quality.

Philosophy:
- DNA Validator = Style (How it looks/sounds)
- Arc Validator = Story (What it means/feels)

License: arkain.info@gmail.com
"""

from typing import Dict, List, Optional, Any
import logging

from app.schemas.narrative import (
    NarrativeArc,
    NarrativePhase,
    ShotNarrativeRole,
    Sequence,
    HookContext,
    ArcType,
    ArcComplianceReport,
    ArcRuleResult,
    get_recommended_hook_contexts,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Arc Compliance Validator
# =============================================================================

class ArcComplianceValidator:
    """서사 구조 준수 검증기"""
    
    # 필수 phase 정의 (arc_type별)
    REQUIRED_PHASES = {
        ArcType.THREE_ACT: {NarrativePhase.HOOK, NarrativePhase.BUILD, NarrativePhase.CLIMAX},
        ArcType.FIVE_ACT: {NarrativePhase.HOOK, NarrativePhase.SETUP, NarrativePhase.BUILD, NarrativePhase.TURN, NarrativePhase.PAYOFF},
        ArcType.HOOK_PAYOFF: {NarrativePhase.HOOK, NarrativePhase.PAYOFF},
        ArcType.MYSTERY: {NarrativePhase.HOOK, NarrativePhase.BUILD, NarrativePhase.TURN},
        ArcType.BUILDUP: {NarrativePhase.HOOK, NarrativePhase.BUILD, NarrativePhase.CLIMAX},
        ArcType.EPISODIC: {NarrativePhase.HOOK},  # 각 시퀀스마다 Hook
    }
    
    def __init__(self):
        self.rule_weights = {
            "hook_coverage": 0.3,
            "phase_coverage": 0.25,
            "expectation_flow": 0.25,
            "emotion_arc": 0.2,
        }
    
    def validate(
        self,
        shots: List[Dict[str, Any]],
        arc: NarrativeArc,
    ) -> ArcComplianceReport:
        """
        서사 구조 준수 검증
        
        Args:
            shots: 샷 계약 리스트 (narrative_role 필드 포함)
            arc: 서사 구조 정의
            
        Returns:
            ArcComplianceReport
        """
        results: List[ArcRuleResult] = []
        
        # 1. Hook 커버리지 검증
        hook_result = self._validate_hook_coverage(shots, arc)
        results.append(hook_result)
        
        # 2. Phase 커버리지 검증
        phase_result = self._validate_phase_coverage(shots, arc)
        results.append(phase_result)
        
        # 3. 기대감 흐름 검증
        expectation_result = self._validate_expectation_flow(shots)
        results.append(expectation_result)
        
        # 4. 감정 곡선 검증
        emotion_result = self._validate_emotion_arc(shots, arc)
        results.append(emotion_result)
        
        # 5. 시퀀스별 Hook 검증 (장편)
        if arc.is_longform and arc.sequences:
            seq_hook_result = self._validate_sequence_hooks(shots, arc)
            results.append(seq_hook_result)
        
        # 전체 결과 계산
        overall_level, overall_confidence = self._calculate_overall(results)
        
        # 누락된 Hook 위치 수집
        missing_hooks = self._find_missing_hooks(shots, arc)
        
        # Hook 커버리지 계산
        hook_coverage = self._calculate_hook_coverage(shots, arc)
        
        # 기대감 충족률 계산
        fulfillment_rate, unfulfilled = self._calculate_expectation_fulfillment(shots)
        
        # 제안 생성
        suggestions = self._generate_suggestions(results, missing_hooks, unfulfilled)
        
        return ArcComplianceReport(
            arc_id=arc.arc_id,
            arc_type=arc.arc_type,
            overall_level=overall_level,
            overall_confidence=overall_confidence,
            rule_results=results,
            hook_coverage=hook_coverage,
            missing_hooks=missing_hooks,
            expectation_fulfillment_rate=fulfillment_rate,
            unfulfilled_expectations=unfulfilled,
            suggestions=suggestions,
        )
    
    def _validate_hook_coverage(
        self,
        shots: List[Dict],
        arc: NarrativeArc,
    ) -> ArcRuleResult:
        """Hook 커버리지 검증"""
        hook_required_shots = []
        hook_present_shots = []
        
        for shot in shots:
            role = shot.get("narrative_role", {})
            if role.get("hook_required") or role.get("is_sequence_start"):
                hook_required_shots.append(shot.get("shot_id", "unknown"))
                if role.get("phase") == "hook":
                    hook_present_shots.append(shot.get("shot_id"))
        
        # 첫 샷은 항상 Hook 필요
        first_shot = shots[0] if shots else {}
        first_phase = first_shot.get("narrative_role", {}).get("phase")
        
        if not hook_required_shots:
            # 암묵적으로 첫 샷은 Hook 필요
            if first_phase == "hook":
                return ArcRuleResult(
                    rule_id="hook_coverage",
                    rule_name="Hook 커버리지",
                    level="compliant",
                    confidence=0.9,
                    message="첫 샷에 Hook 존재",
                    affected_shots=[],
                )
            else:
                return ArcRuleResult(
                    rule_id="hook_coverage",
                    rule_name="Hook 커버리지",
                    level="violation",
                    confidence=0.95,
                    message="첫 샷에 Hook 없음 - 시작부터 시선을 잡아야 합니다",
                    affected_shots=[first_shot.get("shot_id", "shot_001")],
                )
        
        coverage = len(hook_present_shots) / len(hook_required_shots) if hook_required_shots else 0
        missing = set(hook_required_shots) - set(hook_present_shots)
        
        if coverage >= 0.9:
            level = "compliant"
        elif coverage >= 0.6:
            level = "partial"
        else:
            level = "violation"
        
        return ArcRuleResult(
            rule_id="hook_coverage",
            rule_name="Hook 커버리지",
            level=level,
            confidence=min(0.95, coverage + 0.1),
            message=f"Hook 커버리지 {coverage*100:.0f}% ({len(hook_present_shots)}/{len(hook_required_shots)})",
            affected_shots=list(missing),
        )
    
    def _validate_phase_coverage(
        self,
        shots: List[Dict],
        arc: NarrativeArc,
    ) -> ArcRuleResult:
        """서사 단계 커버리지 검증"""
        present_phases = set()
        for shot in shots:
            phase = shot.get("narrative_role", {}).get("phase")
            if phase:
                present_phases.add(phase)
        
        required = self.REQUIRED_PHASES.get(arc.arc_type, {NarrativePhase.HOOK})
        required_strs = {p.value if hasattr(p, 'value') else p for p in required}
        
        missing = required_strs - present_phases
        
        if not missing:
            return ArcRuleResult(
                rule_id="phase_coverage",
                rule_name="서사 단계 커버리지",
                level="compliant",
                confidence=0.9,
                message=f"필수 단계 모두 존재: {', '.join(required_strs)}",
                affected_shots=[],
            )
        
        # Hook 누락은 critical
        if "hook" in missing:
            return ArcRuleResult(
                rule_id="phase_coverage",
                rule_name="서사 단계 커버리지",
                level="violation",
                confidence=0.95,
                message=f"Hook 단계 누락! 시작에서 시선을 잡아야 합니다",
                affected_shots=[],
            )
        
        return ArcRuleResult(
            rule_id="phase_coverage",
            rule_name="서사 단계 커버리지",
            level="partial",
            confidence=0.8,
            message=f"누락된 단계: {', '.join(missing)}",
            affected_shots=[],
        )
    
    def _validate_expectation_flow(
        self,
        shots: List[Dict],
    ) -> ArcRuleResult:
        """기대감 생성-충족 흐름 검증"""
        created = set()
        fulfilled = set()
        
        for shot in shots:
            role = shot.get("narrative_role", {})
            if role.get("expectation_created"):
                created.add(role["expectation_created"])
            if role.get("expectation_fulfilled"):
                fulfilled.add(role["expectation_fulfilled"])
        
        if not created:
            return ArcRuleResult(
                rule_id="expectation_flow",
                rule_name="기대감 흐름",
                level="unknown",
                confidence=0.5,
                message="기대감 정보 없음",
                affected_shots=[],
            )
        
        fulfilled_of_created = created & fulfilled
        rate = len(fulfilled_of_created) / len(created) if created else 0
        unfulfilled = created - fulfilled
        
        if rate >= 0.8:
            level = "compliant"
        elif rate >= 0.5:
            level = "partial"
        else:
            level = "violation"
        
        return ArcRuleResult(
            rule_id="expectation_flow",
            rule_name="기대감 흐름",
            level=level,
            confidence=0.85,
            message=f"기대감 충족률 {rate*100:.0f}%",
            affected_shots=[],
        )
    
    def _validate_emotion_arc(
        self,
        shots: List[Dict],
        arc: NarrativeArc,
    ) -> ArcRuleResult:
        """감정 곡선 검증 (단조롭지 않은지)"""
        emotions = []
        for shot in shots:
            emotion = shot.get("narrative_role", {}).get("target_emotion")
            if emotion:
                emotions.append(emotion)
        
        if len(set(emotions)) <= 1:
            return ArcRuleResult(
                rule_id="emotion_arc",
                rule_name="감정 곡선",
                level="partial",
                confidence=0.7,
                message="감정 변화가 부족합니다 - 다양한 감정을 넣어보세요",
                affected_shots=[],
            )
        
        return ArcRuleResult(
            rule_id="emotion_arc",
            rule_name="감정 곡선",
            level="compliant",
            confidence=0.8,
            message=f"감정 다양성: {len(set(emotions))}가지",
            affected_shots=[],
        )
    
    def _validate_sequence_hooks(
        self,
        shots: List[Dict],
        arc: NarrativeArc,
    ) -> ArcRuleResult:
        """시퀀스별 Hook 검증 (장편)"""
        sequences_with_hooks = 0
        sequences_needing_hooks = 0
        missing_sequences = []
        
        for seq in arc.sequences:
            if seq.hook_recommended:
                sequences_needing_hooks += 1
                # 시퀀스 첫 샷 찾기
                seq_shots = [s for s in shots 
                            if s.get("narrative_role", {}).get("sequence_id") == seq.sequence_id]
                if seq_shots:
                    first_shot_phase = seq_shots[0].get("narrative_role", {}).get("phase")
                    if first_shot_phase == "hook":
                        sequences_with_hooks += 1
                    else:
                        missing_sequences.append(seq.name)
        
        if sequences_needing_hooks == 0:
            return ArcRuleResult(
                rule_id="sequence_hooks",
                rule_name="시퀀스별 Hook",
                level="compliant",
                confidence=0.9,
                message="시퀀스 Hook 검증 해당 없음",
                affected_shots=[],
            )
        
        rate = sequences_with_hooks / sequences_needing_hooks
        
        if rate >= 0.8:
            level = "compliant"
        elif rate >= 0.5:
            level = "partial"
        else:
            level = "violation"
        
        return ArcRuleResult(
            rule_id="sequence_hooks",
            rule_name="시퀀스별 Hook",
            level=level,
            confidence=0.9,
            message=f"시퀀스 Hook 커버리지 {rate*100:.0f}% - 누락: {', '.join(missing_sequences) or '없음'}",
            affected_shots=[],
        )
    
    def _calculate_overall(
        self,
        results: List[ArcRuleResult],
    ) -> tuple:
        """전체 수준 및 신뢰도 계산"""
        if not results:
            return "unknown", 0.5
        
        levels = {"compliant": 0, "partial": 0, "violation": 0, "unknown": 0}
        total_confidence = 0
        
        for r in results:
            levels[r.level] += 1
            total_confidence += r.confidence
        
        avg_confidence = total_confidence / len(results)
        
        if levels["violation"] > 0:
            return "violation", avg_confidence
        elif levels["partial"] > 0:
            return "partial", avg_confidence
        elif levels["compliant"] > 0:
            return "compliant", avg_confidence
        else:
            return "unknown", avg_confidence
    
    def _find_missing_hooks(
        self,
        shots: List[Dict],
        arc: NarrativeArc,
    ) -> List[str]:
        """누락된 Hook 위치 찾기"""
        missing = []
        
        # 첫 샷 체크
        if shots:
            first_phase = shots[0].get("narrative_role", {}).get("phase")
            if first_phase != "hook":
                missing.append("video_start")
        
        # 시퀀스 시작 체크 (장편)
        for seq in arc.sequences:
            if seq.hook_recommended:
                seq_shots = [s for s in shots 
                            if s.get("narrative_role", {}).get("sequence_id") == seq.sequence_id]
                if seq_shots:
                    first_phase = seq_shots[0].get("narrative_role", {}).get("phase")
                    if first_phase != "hook":
                        missing.append(f"sequence:{seq.name}")
        
        return missing
    
    def _calculate_hook_coverage(
        self,
        shots: List[Dict],
        arc: NarrativeArc,
    ) -> float:
        """Hook 커버리지 비율 계산"""
        required = 1  # 최소 첫 샷
        present = 0
        
        if shots and shots[0].get("narrative_role", {}).get("phase") == "hook":
            present += 1
        
        for seq in arc.sequences:
            if seq.hook_recommended:
                required += 1
                seq_shots = [s for s in shots 
                            if s.get("narrative_role", {}).get("sequence_id") == seq.sequence_id]
                if seq_shots and seq_shots[0].get("narrative_role", {}).get("phase") == "hook":
                    present += 1
        
        return present / required if required > 0 else 1.0
    
    def _calculate_expectation_fulfillment(
        self,
        shots: List[Dict],
    ) -> tuple:
        """기대감 충족률 계산"""
        created = set()
        fulfilled = set()
        
        for shot in shots:
            role = shot.get("narrative_role", {})
            if role.get("expectation_created"):
                created.add(role["expectation_created"])
            if role.get("expectation_fulfilled"):
                fulfilled.add(role["expectation_fulfilled"])
        
        if not created:
            return 0.0, []
        
        unfulfilled = list(created - fulfilled)
        rate = len(created & fulfilled) / len(created)
        
        return rate, unfulfilled
    
    def _generate_suggestions(
        self,
        results: List[ArcRuleResult],
        missing_hooks: List[str],
        unfulfilled: List[str],
    ) -> List[str]:
        """개선 제안 생성"""
        suggestions = []
        
        # Hook 관련 제안
        if missing_hooks:
            for hook_loc in missing_hooks:
                if hook_loc == "video_start":
                    suggestions.append("💡 첫 1.5초에 강력한 훅을 추가하세요 - 시작이 승부처입니다!")
                elif hook_loc.startswith("sequence:"):
                    seq_name = hook_loc.replace("sequence:", "")
                    suggestions.append(f"💡 '{seq_name}' 시퀀스 시작에 훅을 추가하면 집중도가 올라갑니다")
        
        # 기대감 관련 제안
        if unfulfilled:
            for exp in unfulfilled[:3]:  # 최대 3개
                suggestions.append(f"❓ 기대감 '{exp}'이 충족되지 않았습니다 - 페이오프를 추가해보세요")
        
        # 일반 제안
        for r in results:
            if r.level == "violation":
                if r.rule_id == "phase_coverage" and "Hook" in r.message:
                    suggestions.append("🔴 시작 샷을 Hook 타입으로 변경하세요")
        
        return suggestions


# =============================================================================
# Factory Function
# =============================================================================

def validate_arc_compliance(
    shots: List[Dict[str, Any]],
    arc: NarrativeArc,
) -> ArcComplianceReport:
    """
    서사 구조 준수 검증 (편의 함수)
    
    사용 예:
    ```python
    report = validate_arc_compliance(shot_contracts, narrative_arc)
    print(f"전체 수준: {report.overall_level}")
    print(f"Hook 커버리지: {report.hook_coverage}")
    ```
    """
    validator = ArcComplianceValidator()
    return validator.validate(shots, arc)
