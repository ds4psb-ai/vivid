"""DNA Compliance Validator

Validates that generated shot contracts comply with DirectorPack DNA rules.
Provides detailed compliance reports for quality assurance.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class ComplianceLevel(str, Enum):
    """Compliance levels for DNA rule checking."""
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    VIOLATION = "violation"
    UNKNOWN = "unknown"


class RulePriority(str, Enum):
    """Rule priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RuleCheckResult:
    """Result of checking a single DNA rule."""
    rule_id: str
    rule_name: str
    priority: RulePriority
    level: ComplianceLevel
    confidence: float
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


@dataclass
class ShotComplianceReport:
    """Compliance report for a single shot."""
    shot_id: str
    overall_level: ComplianceLevel
    overall_confidence: float
    rule_results: List[RuleCheckResult]
    critical_violations: int
    high_violations: int
    suggestions: List[str]


@dataclass
class BatchComplianceReport:
    """Compliance report for multiple shots."""
    total_shots: int
    compliant_shots: int
    partial_shots: int
    violation_shots: int
    overall_compliance_rate: float
    shot_reports: List[ShotComplianceReport]
    summary: str


# =============================================================================
# Rule Extractors from Shot Prompt
# =============================================================================

def extract_timing_info(shot: Dict[str, Any]) -> Dict[str, Any]:
    """Extract timing-related info from shot contract."""
    return {
        "duration_sec": shot.get("duration_sec"),
        "start_time": shot.get("start_time"),
        "end_time": shot.get("end_time"),
        "cuts_per_second": shot.get("cuts_per_second"),
    }


def extract_composition_info(prompt: str) -> Dict[str, Any]:
    """Extract composition info from prompt text."""
    info = {}
    
    # Center composition detection
    center_keywords = ["중앙", "center", "centered", "symmetr", "대칭"]
    info["has_center_composition"] = any(kw in prompt.lower() for kw in center_keywords)
    
    # Vertical blocking
    vertical_keywords = ["수직", "vertical", "위아래", "상하", "층간", "계단"]
    info["has_vertical_blocking"] = any(kw in prompt.lower() for kw in vertical_keywords)
    
    # Rule of thirds
    thirds_keywords = ["삼분할", "rule of thirds", "1/3", "오른쪽 1/3", "왼쪽 1/3"]
    info["has_rule_of_thirds"] = any(kw in prompt.lower() for kw in thirds_keywords)
    
    # Wide shot
    wide_keywords = ["와이드", "wide", "풀샷", "full shot", "에스타블리싱"]
    info["has_wide_shot"] = any(kw in prompt.lower() for kw in wide_keywords)
    
    # Close-up
    closeup_keywords = ["클로즈업", "close-up", "closeup", "접사"]
    info["has_closeup"] = any(kw in prompt.lower() for kw in closeup_keywords)
    
    return info


def extract_camera_info(prompt: str) -> Dict[str, Any]:
    """Extract camera movement info from prompt."""
    info = {}
    
    # Camera movements
    info["has_zoom"] = "줌" in prompt or "zoom" in prompt.lower()
    info["has_pan"] = "팬" in prompt or "pan" in prompt.lower()
    info["has_tilt"] = "틸트" in prompt or "tilt" in prompt.lower()
    info["has_dutch_angle"] = "더치" in prompt or "dutch" in prompt.lower() or "기울" in prompt
    info["has_tracking"] = "트래킹" in prompt or "tracking" in prompt.lower() or "따라가" in prompt
    info["has_push_in"] = "푸시인" in prompt or "push in" in prompt.lower() or "다가가" in prompt
    
    # Lens info
    lens_match = re.search(r'(\d+)mm', prompt)
    info["lens_mm"] = int(lens_match.group(1)) if lens_match else None
    
    return info


def extract_lighting_info(prompt: str) -> Dict[str, Any]:
    """Extract lighting info from prompt."""
    info = {}
    
    info["has_natural_light"] = "자연광" in prompt or "natural" in prompt.lower()
    info["has_backlight"] = "역광" in prompt or "backlight" in prompt.lower()
    info["has_side_light"] = "측광" in prompt or "방향광" in prompt or "side light" in prompt.lower()
    info["has_low_key"] = "로우키" in prompt or "low key" in prompt.lower() or "어두운" in prompt
    info["has_high_key"] = "하이키" in prompt or "high key" in prompt.lower() or "밝은" in prompt
    
    return info


# =============================================================================
# Rule Validators
# =============================================================================

def validate_timing_rule(
    rule: Dict[str, Any],
    shot: Dict[str, Any],
) -> RuleCheckResult:
    """Validate a timing-related DNA rule."""
    rule_id = rule.get("rule_id", "unknown")
    rule_name = rule.get("name", rule_id)
    priority = RulePriority(rule.get("priority", "medium"))
    spec = rule.get("spec", {})
    condition = rule.get("condition", "")
    
    timing = extract_timing_info(shot)
    
    # Hook timing check
    if "hook" in condition.lower():
        hook_time = timing.get("start_time", 0)
        threshold = spec.get("value", 2.0)
        operator = spec.get("operator", "<=")
        
        if hook_time is None:
            return RuleCheckResult(
                rule_id=rule_id,
                rule_name=rule_name,
                priority=priority,
                level=ComplianceLevel.UNKNOWN,
                confidence=0.5,
                message="Hook time not specified in shot",
            )
        
        if operator in ("<=", "lte"):
            compliant = hook_time <= threshold
        elif operator in (">=", "gte"):
            compliant = hook_time >= threshold
        else:
            compliant = hook_time == threshold
        
        return RuleCheckResult(
            rule_id=rule_id,
            rule_name=rule_name,
            priority=priority,
            level=ComplianceLevel.COMPLIANT if compliant else ComplianceLevel.VIOLATION,
            confidence=0.9 if hook_time is not None else 0.5,
            message=f"Hook at {hook_time}s ({'✓' if compliant else '✗'} {threshold}s)",
            expected=f"{operator} {threshold}",
            actual=hook_time,
        )
    
    # Cut frequency check
    if "cuts" in condition.lower() or "cut" in condition.lower():
        cuts = timing.get("cuts_per_second", 0.3)
        threshold = spec.get("value", 0.5)
        
        compliant = cuts <= threshold
        return RuleCheckResult(
            rule_id=rule_id,
            rule_name=rule_name,
            priority=priority,
            level=ComplianceLevel.COMPLIANT if compliant else ComplianceLevel.VIOLATION,
            confidence=0.7,
            message=f"Cut frequency {cuts}/sec ({'✓' if compliant else '✗'} {threshold})",
            expected=f"<= {threshold}",
            actual=cuts,
        )
    
    return RuleCheckResult(
        rule_id=rule_id,
        rule_name=rule_name,
        priority=priority,
        level=ComplianceLevel.UNKNOWN,
        confidence=0.3,
        message="Could not validate timing rule",
    )


def validate_composition_rule(
    rule: Dict[str, Any],
    shot: Dict[str, Any],
) -> RuleCheckResult:
    """Validate a composition-related DNA rule."""
    rule_id = rule.get("rule_id", "unknown")
    rule_name = rule.get("name", rule_id)
    priority = RulePriority(rule.get("priority", "medium"))
    condition = rule.get("condition", "")
    
    prompt = shot.get("prompt", "") or shot.get("visual_prompt", "")
    comp = extract_composition_info(prompt)
    
    # Center composition
    if "center" in condition.lower() or "중앙" in rule_name:
        compliant = comp.get("has_center_composition", False)
        return RuleCheckResult(
            rule_id=rule_id,
            rule_name=rule_name,
            priority=priority,
            level=ComplianceLevel.COMPLIANT if compliant else ComplianceLevel.PARTIAL,
            confidence=0.8 if compliant else 0.6,
            message="중앙 구도 감지됨" if compliant else "중앙 구도 불명확",
            expected="center composition",
            actual="detected" if compliant else "not detected",
        )
    
    # Vertical blocking
    if "vertical" in condition.lower() or "수직" in rule_name:
        compliant = comp.get("has_vertical_blocking", False)
        return RuleCheckResult(
            rule_id=rule_id,
            rule_name=rule_name,
            priority=priority,
            level=ComplianceLevel.COMPLIANT if compliant else ComplianceLevel.PARTIAL,
            confidence=0.75 if compliant else 0.5,
            message="수직 블로킹 감지됨" if compliant else "수직 블로킹 불명확",
            expected="vertical blocking",
            actual="detected" if compliant else "not detected",
        )
    
    return RuleCheckResult(
        rule_id=rule_id,
        rule_name=rule_name,
        priority=priority,
        level=ComplianceLevel.UNKNOWN,
        confidence=0.3,
        message="Could not validate composition rule",
    )


def validate_forbidden_mutation(
    forbidden: Dict[str, Any],
    shot: Dict[str, Any],
) -> RuleCheckResult:
    """Validate that a forbidden mutation is not present."""
    mutation_id = forbidden.get("mutation_id", "unknown")
    mutation_name = forbidden.get("name", mutation_id)
    severity = forbidden.get("severity", "major")
    forbidden_condition = forbidden.get("forbidden_condition", "")
    
    prompt = shot.get("prompt", "") or shot.get("visual_prompt", "")
    camera = extract_camera_info(prompt)
    
    priority = RulePriority.CRITICAL if severity == "critical" else (
        RulePriority.HIGH if severity == "major" else RulePriority.MEDIUM
    )
    
    # Jump cut check
    if "jump" in mutation_id.lower():
        has_violation = "점프컷" in prompt.lower() or "jump cut" in prompt.lower()
        return RuleCheckResult(
            rule_id=mutation_id,
            rule_name=mutation_name,
            priority=priority,
            level=ComplianceLevel.VIOLATION if has_violation else ComplianceLevel.COMPLIANT,
            confidence=0.85,
            message="점프컷 금지 위반" if has_violation else "점프컷 없음 ✓",
        )
    
    # Dutch angle check
    if "dutch" in mutation_id.lower():
        has_violation = camera.get("has_dutch_angle", False)
        return RuleCheckResult(
            rule_id=mutation_id,
            rule_name=mutation_name,
            priority=priority,
            level=ComplianceLevel.VIOLATION if has_violation else ComplianceLevel.COMPLIANT,
            confidence=0.9,
            message="더치 앵글 금지 위반" if has_violation else "더치 앵글 없음 ✓",
        )
    
    # Fast zoom check
    if "zoom" in mutation_id.lower():
        has_violation = camera.get("has_zoom", False) and "빠른" in prompt
        return RuleCheckResult(
            rule_id=mutation_id,
            rule_name=mutation_name,
            priority=priority,
            level=ComplianceLevel.VIOLATION if has_violation else ComplianceLevel.COMPLIANT,
            confidence=0.7,
            message="빠른 줌 금지 위반" if has_violation else "빠른 줌 없음 ✓",
        )
    
    return RuleCheckResult(
        rule_id=mutation_id,
        rule_name=mutation_name,
        priority=priority,
        level=ComplianceLevel.UNKNOWN,
        confidence=0.3,
        message="Could not validate forbidden mutation",
    )


# =============================================================================
# Main Validator
# =============================================================================

def validate_shot_compliance(
    shot: Dict[str, Any],
    director_pack: Dict[str, Any],
) -> ShotComplianceReport:
    """
    Validate a single shot's compliance with DirectorPack DNA rules.
    
    Args:
        shot: Shot contract containing prompt, duration, etc.
        director_pack: DirectorPack with dna_invariants and forbidden_mutations
        
    Returns:
        ShotComplianceReport with detailed rule check results
    """
    shot_id = shot.get("shot_id", "unknown")
    results: List[RuleCheckResult] = []
    
    # Check DNA invariants
    invariants = director_pack.get("dna_invariants", [])
    for inv in invariants:
        rule_type = inv.get("rule_type", "")
        
        if rule_type == "timing":
            results.append(validate_timing_rule(inv, shot))
        elif rule_type == "composition":
            results.append(validate_composition_rule(inv, shot))
        else:
            # Generic check - look for keywords in prompt
            prompt = shot.get("prompt", "") or shot.get("visual_prompt", "")
            rule_id = inv.get("rule_id", "")
            rule_name = inv.get("name", rule_id)
            
            # Simple keyword matching
            keywords = rule_name.lower().split()
            found = any(kw in prompt.lower() for kw in keywords if len(kw) > 2)
            
            results.append(RuleCheckResult(
                rule_id=rule_id,
                rule_name=rule_name,
                priority=RulePriority(inv.get("priority", "medium")),
                level=ComplianceLevel.PARTIAL if found else ComplianceLevel.UNKNOWN,
                confidence=0.5,
                message=f"Rule '{rule_name}' keyword check",
            ))
    
    # Check forbidden mutations
    forbidden = director_pack.get("forbidden_mutations", [])
    for forb in forbidden:
        results.append(validate_forbidden_mutation(forb, shot))
    
    # Calculate overall compliance
    critical_violations = sum(
        1 for r in results
        if r.level == ComplianceLevel.VIOLATION and r.priority == RulePriority.CRITICAL
    )
    high_violations = sum(
        1 for r in results
        if r.level == ComplianceLevel.VIOLATION and r.priority == RulePriority.HIGH
    )
    
    compliant_count = sum(1 for r in results if r.level == ComplianceLevel.COMPLIANT)
    total_checked = len([r for r in results if r.level != ComplianceLevel.UNKNOWN])
    
    if critical_violations > 0:
        overall_level = ComplianceLevel.VIOLATION
    elif high_violations > 0:
        overall_level = ComplianceLevel.PARTIAL
    elif total_checked > 0 and compliant_count == total_checked:
        overall_level = ComplianceLevel.COMPLIANT
    elif total_checked > 0:
        overall_level = ComplianceLevel.PARTIAL
    else:
        overall_level = ComplianceLevel.UNKNOWN
    
    # Calculate confidence
    if results:
        overall_confidence = sum(r.confidence for r in results) / len(results)
    else:
        overall_confidence = 0.0
    
    # Generate suggestions
    suggestions = []
    for r in results:
        if r.level == ComplianceLevel.VIOLATION:
            inv = next((i for i in invariants if i.get("rule_id") == r.rule_id), None)
            if inv and inv.get("coach_line_ko"):
                suggestions.append(inv["coach_line_ko"])
            else:
                suggestions.append(f"Fix: {r.message}")
    
    return ShotComplianceReport(
        shot_id=shot_id,
        overall_level=overall_level,
        overall_confidence=overall_confidence,
        rule_results=results,
        critical_violations=critical_violations,
        high_violations=high_violations,
        suggestions=suggestions,
    )


def validate_batch_compliance(
    shots: List[Dict[str, Any]],
    director_pack: Dict[str, Any],
) -> BatchComplianceReport:
    """
    Validate multiple shots for DNA compliance.
    
    Args:
        shots: List of shot contracts
        director_pack: DirectorPack with DNA rules
        
    Returns:
        BatchComplianceReport with per-shot details and summary
    """
    shot_reports = [validate_shot_compliance(shot, director_pack) for shot in shots]
    
    compliant = sum(1 for r in shot_reports if r.overall_level == ComplianceLevel.COMPLIANT)
    partial = sum(1 for r in shot_reports if r.overall_level == ComplianceLevel.PARTIAL)
    violations = sum(1 for r in shot_reports if r.overall_level == ComplianceLevel.VIOLATION)
    
    total = len(shots)
    compliance_rate = compliant / total if total > 0 else 0.0
    
    # Generate summary
    if compliance_rate >= 0.9:
        summary = "✅ 높은 DNA 준수율 - 일관된 스타일 유지"
    elif compliance_rate >= 0.7:
        summary = "⚠️ 보통 DNA 준수율 - 일부 개선 필요"
    elif compliance_rate >= 0.5:
        summary = "⚠️ 낮은 DNA 준수율 - 상당한 조정 필요"
    else:
        summary = "❌ 심각한 DNA 불일치 - 재생성 권장"
    
    return BatchComplianceReport(
        total_shots=total,
        compliant_shots=compliant,
        partial_shots=partial,
        violation_shots=violations,
        overall_compliance_rate=compliance_rate,
        shot_reports=shot_reports,
        summary=summary,
    )


# =============================================================================
# Convenience Functions
# =============================================================================

def get_compliance_badge(level: ComplianceLevel) -> str:
    """Get emoji badge for compliance level."""
    return {
        ComplianceLevel.COMPLIANT: "✅",
        ComplianceLevel.PARTIAL: "⚠️",
        ComplianceLevel.VIOLATION: "❌",
        ComplianceLevel.UNKNOWN: "❓",
    }.get(level, "❓")


def format_compliance_report(report: ShotComplianceReport) -> str:
    """Format a shot compliance report as readable text."""
    badge = get_compliance_badge(report.overall_level)
    lines = [
        f"{badge} Shot: {report.shot_id}",
        f"   Overall: {report.overall_level.value} (confidence: {report.overall_confidence:.0%})",
        f"   Critical violations: {report.critical_violations}",
        f"   High violations: {report.high_violations}",
    ]
    
    if report.suggestions:
        lines.append("   Suggestions:")
        for s in report.suggestions[:3]:
            lines.append(f"     - {s}")
    
    return "\n".join(lines)
