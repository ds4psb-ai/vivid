"""
Story-First Compliance Validator

Unified validator that combines:
1. DNA Validator - Style compliance (visual rules, timing, composition)
2. Arc Validator - Narrative compliance (structure, hooks, emotions)

Produces comprehensive StoryFirstComplianceReport with:
- Overall grade (A-F)
- DNA score + Arc score
- Combined suggestions
- Export formats: JSON, Markdown

License: arkain.info@gmail.com
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import logging
import json

from app.services.dna_validator import (
    validate_batch_compliance,
    BatchComplianceReport,
    ComplianceLevel,
    get_compliance_badge,
)
from app.services.arc_validator import (
    ArcComplianceValidator,
    validate_arc_compliance,
)
from app.schemas.narrative import (
    NarrativeArc,
    ArcType,
    NarrativePhase,
    ArcComplianceReport,
    ArcRuleResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Types
# =============================================================================

class OverallGrade(str, Enum):
    """Overall compliance grade"""
    A = "A"  # 90-100%
    B = "B"  # 80-89%
    C = "C"  # 70-79%
    D = "D"  # 60-69%
    F = "F"  # Below 60%


@dataclass
class StoryFirstComplianceReport:
    """
    통합 Story-First + DNA 준수 리포트
    """
    # Scores
    total_score: float  # 0-100
    dna_score: float    # 0-100
    arc_score: float    # 0-100
    grade: OverallGrade
    
    # DNA Details
    dna_compliant_shots: int
    dna_total_shots: int
    dna_critical_violations: int
    dna_high_violations: int
    
    # Arc Details
    arc_hook_coverage: float      # 0-1
    arc_expectation_fulfillment: float  # 0-1
    arc_missing_hooks: List[str]
    arc_unfulfilled_expectations: List[str]
    
    # Combined Suggestions
    suggestions: List[str]
    priority_fixes: List[str]  # Top 3 critical issues
    
    # Raw reports
    dna_report: Optional[BatchComplianceReport] = None
    arc_report: Optional[ArcComplianceReport] = None
    
    # Meta
    shot_count: int = 0
    director_pack_id: Optional[str] = None
    arc_type: Optional[str] = None


# =============================================================================
# Validator
# =============================================================================

class StoryFirstValidator:
    """
    DNA + Arc 통합 검증기
    
    Usage:
    ```python
    validator = StoryFirstValidator()
    report = validator.validate(
        shots=shot_contracts,
        director_pack=director_pack,
        narrative_arc=narrative_arc,
    )
    print(f"Total Score: {report.total_score}")
    print(f"Grade: {report.grade}")
    ```
    """
    
    def __init__(
        self,
        dna_weight: float = 0.4,   # DNA 40%
        arc_weight: float = 0.6,   # Arc 60% (story-first!)
    ):
        self.dna_weight = dna_weight
        self.arc_weight = arc_weight
        self.arc_validator = ArcComplianceValidator()
    
    def validate(
        self,
        shots: List[Dict[str, Any]],
        director_pack: Optional[Dict[str, Any]] = None,
        narrative_arc: Optional[NarrativeArc] = None,
    ) -> StoryFirstComplianceReport:
        """
        통합 검증 수행
        
        Args:
            shots: Shot contracts with prompts and narrative_role
            director_pack: DirectorPack with dna_invariants
            narrative_arc: NarrativeArc with arc_type, sequences
            
        Returns:
            StoryFirstComplianceReport with combined scores
        """
        # DNA Validation
        dna_score = 100.0
        dna_compliant = 0
        dna_critical = 0
        dna_high = 0
        dna_report = None
        dna_suggestions = []
        
        if director_pack and shots:
            dna_report = validate_batch_compliance(shots, director_pack)
            dna_score = dna_report.overall_compliance_rate * 100
            dna_compliant = dna_report.compliant_shots
            
            # Count violations
            for shot_report in dna_report.shot_reports:
                dna_critical += shot_report.critical_violations
                dna_high += shot_report.high_violations
                dna_suggestions.extend(shot_report.suggestions[:2])
        
        # Arc Validation
        arc_score = 100.0
        arc_hook_coverage = 1.0
        arc_expectation_fulfillment = 1.0
        arc_missing_hooks = []
        arc_unfulfilled = []
        arc_report = None
        arc_suggestions = []
        
        if narrative_arc and shots:
            arc_report = self.arc_validator.validate(shots, narrative_arc)
            arc_score = arc_report.overall_confidence * 100
            arc_hook_coverage = arc_report.hook_coverage
            arc_expectation_fulfillment = arc_report.expectation_fulfillment_rate
            arc_missing_hooks = arc_report.missing_hooks
            arc_unfulfilled = arc_report.unfulfilled_expectations
            arc_suggestions = arc_report.suggestions
        
        # Combined Score (weighted)
        if director_pack and narrative_arc:
            total_score = (self.dna_weight * dna_score) + (self.arc_weight * arc_score)
        elif director_pack:
            total_score = dna_score
        elif narrative_arc:
            total_score = arc_score
        else:
            total_score = 100.0
        
        # Grade
        grade = self._calculate_grade(total_score, dna_critical, arc_missing_hooks)
        
        # Combine suggestions
        all_suggestions = []
        all_suggestions.extend([f"🎬 {s}" for s in arc_suggestions[:3]])
        all_suggestions.extend([f"🎨 {s}" for s in dna_suggestions[:3]])
        
        # Priority fixes (top 3 critical issues)
        priority_fixes = self._get_priority_fixes(
            dna_critical, dna_high, arc_missing_hooks, arc_unfulfilled
        )
        
        return StoryFirstComplianceReport(
            total_score=round(total_score, 1),
            dna_score=round(dna_score, 1),
            arc_score=round(arc_score, 1),
            grade=grade,
            dna_compliant_shots=dna_compliant,
            dna_total_shots=len(shots),
            dna_critical_violations=dna_critical,
            dna_high_violations=dna_high,
            arc_hook_coverage=round(arc_hook_coverage, 2),
            arc_expectation_fulfillment=round(arc_expectation_fulfillment, 2),
            arc_missing_hooks=arc_missing_hooks,
            arc_unfulfilled_expectations=arc_unfulfilled,
            suggestions=all_suggestions,
            priority_fixes=priority_fixes,
            dna_report=dna_report,
            arc_report=arc_report,
            shot_count=len(shots),
            director_pack_id=director_pack.get("meta", {}).get("pack_id") if director_pack else None,
            arc_type=narrative_arc.arc_type.value if narrative_arc else None,
        )
    
    def _calculate_grade(
        self,
        total_score: float,
        dna_critical: int,
        arc_missing_hooks: List[str],
    ) -> OverallGrade:
        """Calculate letter grade with penalty for critical issues"""
        # Critical violations cap grade at C
        if dna_critical > 0:
            total_score = min(total_score, 79)
        
        # Missing hooks cap grade at B
        if arc_missing_hooks:
            total_score = min(total_score, 89)
        
        if total_score >= 90:
            return OverallGrade.A
        elif total_score >= 80:
            return OverallGrade.B
        elif total_score >= 70:
            return OverallGrade.C
        elif total_score >= 60:
            return OverallGrade.D
        else:
            return OverallGrade.F
    
    def _get_priority_fixes(
        self,
        dna_critical: int,
        dna_high: int,
        arc_missing_hooks: List[str],
        arc_unfulfilled: List[str],
    ) -> List[str]:
        """Get top priority issues to fix"""
        fixes = []
        
        if arc_missing_hooks:
            fixes.append(f"🎯 첫 번째 훅 필요: {arc_missing_hooks[0]}")
        
        if dna_critical > 0:
            fixes.append(f"⛔ DNA 치명적 위반 {dna_critical}건 수정 필요")
        
        if arc_unfulfilled:
            fixes.append(f"❓ 미충족 기대감: '{arc_unfulfilled[0]}'")
        
        if dna_high > 0:
            fixes.append(f"⚠️ DNA 높은 위반 {dna_high}건 검토")
        
        return fixes[:3]


# =============================================================================
# Export Functions
# =============================================================================

def report_to_json(report: StoryFirstComplianceReport) -> Dict[str, Any]:
    """Convert report to JSON-serializable dict"""
    return {
        "total_score": report.total_score,
        "grade": report.grade.value,
        "dna_score": report.dna_score,
        "arc_score": report.arc_score,
        "shot_count": report.shot_count,
        "dna": {
            "compliant_shots": report.dna_compliant_shots,
            "total_shots": report.dna_total_shots,
            "critical_violations": report.dna_critical_violations,
            "high_violations": report.dna_high_violations,
        },
        "arc": {
            "hook_coverage": report.arc_hook_coverage,
            "expectation_fulfillment": report.arc_expectation_fulfillment,
            "missing_hooks": report.arc_missing_hooks,
            "unfulfilled_expectations": report.arc_unfulfilled_expectations,
        },
        "suggestions": report.suggestions,
        "priority_fixes": report.priority_fixes,
        "meta": {
            "director_pack_id": report.director_pack_id,
            "arc_type": report.arc_type,
        }
    }


def report_to_markdown(report: StoryFirstComplianceReport) -> str:
    """Convert report to readable markdown"""
    grade_emoji = {
        OverallGrade.A: "🏆",
        OverallGrade.B: "✅",
        OverallGrade.C: "⚠️",
        OverallGrade.D: "🔶",
        OverallGrade.F: "❌",
    }
    
    lines = [
        f"# Story-First 준수 리포트",
        "",
        f"## {grade_emoji[report.grade]} 종합 등급: {report.grade.value} ({report.total_score}점)",
        "",
        "| 구분 | 점수 |",
        "|------|------|",
        f"| 🎨 DNA (스타일) | {report.dna_score}점 |",
        f"| 🎬 Arc (서사) | {report.arc_score}점 |",
        f"| 📊 총점 | **{report.total_score}점** |",
        "",
    ]
    
    # DNA Details
    lines.extend([
        "## 🎨 DNA 준수 현황",
        "",
        f"- 준수 샷: {report.dna_compliant_shots}/{report.dna_total_shots}",
        f"- 치명적 위반: {report.dna_critical_violations}건",
        f"- 높은 위반: {report.dna_high_violations}건",
        "",
    ])
    
    # Arc Details
    lines.extend([
        "## 🎬 서사 준수 현황",
        "",
        f"- Hook 커버리지: {report.arc_hook_coverage * 100:.0f}%",
        f"- 기대감 충족률: {report.arc_expectation_fulfillment * 100:.0f}%",
    ])
    
    if report.arc_missing_hooks:
        lines.append(f"- ❌ 누락된 Hook: {', '.join(report.arc_missing_hooks)}")
    
    if report.arc_unfulfilled_expectations:
        lines.append(f"- ❌ 미충족 기대감: {', '.join(report.arc_unfulfilled_expectations[:3])}")
    
    lines.append("")
    
    # Priority Fixes
    if report.priority_fixes:
        lines.extend([
            "## 🔧 우선 수정 사항",
            "",
        ])
        for i, fix in enumerate(report.priority_fixes, 1):
            lines.append(f"{i}. {fix}")
        lines.append("")
    
    # Suggestions
    if report.suggestions:
        lines.extend([
            "## 💡 개선 제안",
            "",
        ])
        for sugg in report.suggestions:
            lines.append(f"- {sugg}")
    
    return "\n".join(lines)


# =============================================================================
# Convenience Function
# =============================================================================

def validate_story_first(
    shots: List[Dict[str, Any]],
    director_pack: Optional[Dict[str, Any]] = None,
    narrative_arc: Optional[NarrativeArc] = None,
    dna_weight: float = 0.4,
    arc_weight: float = 0.6,
) -> StoryFirstComplianceReport:
    """
    Story-First 통합 검증 (편의 함수)
    
    Usage:
    ```python
    report = validate_story_first(
        shots=shot_contracts,
        director_pack=bong_pack,
        narrative_arc=arc,
    )
    
    print(f"Grade: {report.grade}")
    print(report_to_markdown(report))
    ```
    """
    validator = StoryFirstValidator(dna_weight=dna_weight, arc_weight=arc_weight)
    return validator.validate(shots, director_pack, narrative_arc)
