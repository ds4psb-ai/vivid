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
# Keyword Dictionaries (Bilingual: Korean + English)
# =============================================================================

COMPOSITION_KEYWORDS = {
    "center": {
        "ko": ["중앙", "중심", "가운데", "센터", "대칭", "정중앙", "한가운데"],
        "en": ["center", "centered", "central", "middle", "symmetric", "symmetrical"],
        "patterns": [
            r"(중앙|center)[\s]*배치",
            r"화면[\s]*(중앙|가운데)",
            r"(대칭|symmetr)",
        ]
    },
    "vertical": {
        "ko": ["수직", "위아래", "상하", "층간", "계단", "높이", "수직선", "위쪽", "아래쪽"],
        "en": ["vertical", "top-bottom", "staircase", "stairs", "height", "layered", "levels"],
        "patterns": [
            r"(위|아래)[\s]*공간",
            r"층[\s]*간",
            r"수직[\s]*(공간|블로킹|배치)",
        ]
    },
    "thirds": {
        "ko": ["삼분할", "1/3", "3분할", "황금분할"],
        "en": ["rule of thirds", "third", "thirds", "golden ratio"],
        "patterns": [
            r"(오른쪽|왼쪽)[\s]*1/3",
            r"(상단|하단)[\s]*1/3",
        ]
    },
    "wide": {
        "ko": ["와이드", "풀샷", "전경", "에스타블리싱", "넓은", "광각", "원경"],
        "en": ["wide", "full shot", "establishing", "panorama", "panoramic", "long shot"],
        "patterns": [
            r"wide[\s]*shot",
            r"full[\s]*shot",
            r"establishing[\s]*shot",
        ]
    },
    "closeup": {
        "ko": ["클로즈업", "접사", "근접", "얼굴", "디테일", "익스트림", "바스트"],
        "en": ["close-up", "closeup", "close up", "extreme closeup", "detail", "bust shot"],
        "patterns": [
            r"close[\s\-]*up",
            r"extreme[\s]*close",
        ]
    },
    "depth": {
        "ko": ["깊은", "심도", "포커스", "전경", "후경", "중경", "레이어"],
        "en": ["deep", "depth", "focus", "foreground", "background", "midground", "layered"],
        "patterns": [
            r"(전|중|후)경",
            r"(deep|shallow)[\s]*focus",
        ]
    },
    "framing": {
        "ko": ["프레이밍", "프레임", "구도", "자연", "문", "창문", "통로"],
        "en": ["framing", "frame", "doorway", "window", "archway", "natural frame"],
        "patterns": [
            r"(창문|문|통로)[\s]*(을[\s]*통해|으로)",
            r"natural[\s]*frame",
        ]
    },
}

CAMERA_KEYWORDS = {
    "zoom": {
        "ko": ["줌", "줌인", "줌아웃", "확대", "축소"],
        "en": ["zoom", "zoom in", "zoom out", "zooming"],
        "patterns": [r"(줌|zoom)[\s]*(인|아웃|in|out)?"]
    },
    "pan": {
        "ko": ["팬", "패닝", "좌우", "수평이동"],
        "en": ["pan", "panning", "horizontal"],
        "patterns": [r"(팬|pan)[\s]*(좌|우|left|right)?"]
    },
    "tilt": {
        "ko": ["틸트", "틸팅", "상하이동"],
        "en": ["tilt", "tilting"],
        "patterns": [r"(틸트|tilt)[\s]*(업|다운|up|down)?"]
    },
    "dutch": {
        "ko": ["더치", "기울", "사선", "비스듬"],
        "en": ["dutch", "dutch angle", "canted", "oblique", "tilted"],
        "patterns": [r"(더치|dutch)[\s]*(앵글|angle)?", r"카메라[\s]*기울"]
    },
    "tracking": {
        "ko": ["트래킹", "따라가", "추적", "팔로우"],
        "en": ["tracking", "follow", "following"],
        "patterns": [r"(tracking|follow)[\s]*shot", r"따라가[\s]*(는|며)"]
    },
    "push": {
        "ko": ["푸시인", "다가가", "접근", "전진"],
        "en": ["push in", "dolly in", "push", "approach"],
        "patterns": [r"(push|dolly)[\s]*in", r"(다가|전진)[\s]*(가|하)"]
    },
    "pullback": {
        "ko": ["풀백", "뒤로", "후퇴", "물러나"],
        "en": ["pull back", "dolly out", "pullback", "retreat"],
        "patterns": [r"(pull|dolly)[\s]*(back|out)"]
    },
    "crane": {
        "ko": ["크레인", "지브", "상승", "하강"],
        "en": ["crane", "jib", "rising", "descending"],
        "patterns": [r"(crane|jib)[\s]*shot"]
    },
    "handheld": {
        "ko": ["핸드헬드", "손흔들림", "다큐", "리얼리티"],
        "en": ["handheld", "shaky", "documentary", "verité"],
        "patterns": [r"hand[\s]*held"]
    },
    "steadicam": {
        "ko": ["스테디캠", "짐벌", "안정", "부드러운"],
        "en": ["steadicam", "gimbal", "stabilized", "smooth"],
        "patterns": [r"steadi[\s]*cam"]
    },
}

LIGHTING_KEYWORDS = {
    "natural": {
        "ko": ["자연광", "햇빛", "햇살", "일광", "창문광"],
        "en": ["natural", "sunlight", "daylight", "window light", "ambient"],
        "patterns": [r"(자연|natural)[\s]*(광|light)"]
    },
    "backlight": {
        "ko": ["역광", "실루엣", "후광", "뒤에서"],
        "en": ["backlight", "backlighting", "silhouette", "rim light"],
        "patterns": [r"back[\s]*light", r"역[\s]*광"]
    },
    "side": {
        "ko": ["측광", "방향광", "옆에서", "측면"],
        "en": ["side light", "directional", "lateral", "key light"],
        "patterns": [r"side[\s]*light", r"(측|방향)[\s]*광"]
    },
    "low_key": {
        "ko": ["로우키", "어두운", "그림자", "명암", "무드", "어둠"],
        "en": ["low key", "dark", "shadow", "moody", "chiaroscuro", "noir"],
        "patterns": [r"low[\s]*key", r"(어둡|어두운|그림자)"]
    },
    "high_key": {
        "ko": ["하이키", "밝은", "화사한", "환한", "고조도"],
        "en": ["high key", "bright", "luminous", "overexposed", "soft light"],
        "patterns": [r"high[\s]*key", r"(밝|환|화사)"]
    },
    "practical": {
        "ko": ["실용광", "램프", "조명기구", "네온"],
        "en": ["practical", "lamp", "neon", "in-frame light"],
        "patterns": [r"practical[\s]*light"]
    },
    "motivated": {
        "ko": ["동기화광", "창문", "문틈", "틈새"],
        "en": ["motivated", "motivated light", "source light"],
        "patterns": [r"(창문|문)[\s]*(에서|으로)[\s]*들어"]
    },
}

COLOR_KEYWORDS = {
    "warm": {
        "ko": ["따뜻한", "웜톤", "노란", "주황", "갈색"],
        "en": ["warm", "orange", "yellow", "amber", "golden"],
        "patterns": [r"(따뜻|warm)[\s]*(한|tone)?"]
    },
    "cool": {
        "ko": ["차가운", "쿨톤", "파란", "청색", "차분한"],
        "en": ["cool", "cold", "blue", "cyan", "teal"],
        "patterns": [r"(차가|cool|cold)[\s]*(운|tone)?"]
    },
    "desaturated": {
        "ko": ["저채도", "무채색", "흑백", "모노"],
        "en": ["desaturated", "muted", "monochrome", "grayscale", "b&w"],
        "patterns": [r"(저|low)[\s]*채도", r"(흑|black)[\s]*백"]
    },
    "vibrant": {
        "ko": ["선명한", "생동감", "채도", "화려한"],
        "en": ["vibrant", "saturated", "vivid", "colorful", "punchy"],
        "patterns": [r"(선명|vibrant|vivid)"]
    },
}


# =============================================================================
# Rule Extractors from Shot Prompt
# =============================================================================

def match_keywords(prompt: str, keyword_dict: dict) -> bool:
    """
    Check if prompt contains any keywords from the keyword dictionary.
    Supports bilingual (ko/en) keywords and regex patterns.
    """
    prompt_lower = prompt.lower()
    
    # Check Korean keywords
    for kw in keyword_dict.get("ko", []):
        if kw in prompt:  # Korean is case-sensitive
            return True
    
    # Check English keywords
    for kw in keyword_dict.get("en", []):
        if kw in prompt_lower:
            return True
    
    # Check regex patterns
    for pattern in keyword_dict.get("patterns", []):
        if re.search(pattern, prompt, re.IGNORECASE):
            return True
    
    return False


def extract_timing_info(shot: Dict[str, Any]) -> Dict[str, Any]:
    """Extract timing-related info from shot contract."""
    prompt = shot.get("prompt", "") or shot.get("visual_prompt", "")
    
    # Try to extract duration from prompt
    duration = shot.get("duration_sec")
    if duration is None:
        # Try regex extraction
        dur_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:초|sec|s)\b', prompt)
        if dur_match:
            duration = float(dur_match.group(1))
    
    return {
        "duration_sec": duration,
        "start_time": shot.get("start_time"),
        "end_time": shot.get("end_time"),
        "cuts_per_second": shot.get("cuts_per_second"),
    }


def extract_composition_info(prompt: str) -> Dict[str, Any]:
    """Extract composition info from prompt text using comprehensive keyword matching."""
    info = {}
    
    info["has_center_composition"] = match_keywords(prompt, COMPOSITION_KEYWORDS["center"])
    info["has_vertical_blocking"] = match_keywords(prompt, COMPOSITION_KEYWORDS["vertical"])
    info["has_rule_of_thirds"] = match_keywords(prompt, COMPOSITION_KEYWORDS["thirds"])
    info["has_wide_shot"] = match_keywords(prompt, COMPOSITION_KEYWORDS["wide"])
    info["has_closeup"] = match_keywords(prompt, COMPOSITION_KEYWORDS["closeup"])
    info["has_depth"] = match_keywords(prompt, COMPOSITION_KEYWORDS["depth"])
    info["has_framing"] = match_keywords(prompt, COMPOSITION_KEYWORDS["framing"])
    
    return info


def extract_camera_info(prompt: str) -> Dict[str, Any]:
    """Extract camera movement info from prompt using comprehensive keyword matching."""
    info = {}
    
    info["has_zoom"] = match_keywords(prompt, CAMERA_KEYWORDS["zoom"])
    info["has_pan"] = match_keywords(prompt, CAMERA_KEYWORDS["pan"])
    info["has_tilt"] = match_keywords(prompt, CAMERA_KEYWORDS["tilt"])
    info["has_dutch_angle"] = match_keywords(prompt, CAMERA_KEYWORDS["dutch"])
    info["has_tracking"] = match_keywords(prompt, CAMERA_KEYWORDS["tracking"])
    info["has_push_in"] = match_keywords(prompt, CAMERA_KEYWORDS["push"])
    info["has_pullback"] = match_keywords(prompt, CAMERA_KEYWORDS["pullback"])
    info["has_crane"] = match_keywords(prompt, CAMERA_KEYWORDS["crane"])
    info["has_handheld"] = match_keywords(prompt, CAMERA_KEYWORDS["handheld"])
    info["has_steadicam"] = match_keywords(prompt, CAMERA_KEYWORDS["steadicam"])
    
    # Lens info
    lens_match = re.search(r'(\d+)\s*mm', prompt, re.IGNORECASE)
    info["lens_mm"] = int(lens_match.group(1)) if lens_match else None
    
    # Speed modifiers
    info["is_fast"] = bool(re.search(r'(빠른|빠르게|fast|rapid|quick)', prompt, re.IGNORECASE))
    info["is_slow"] = bool(re.search(r'(느린|천천히|slow|gentle|subtle)', prompt, re.IGNORECASE))
    
    return info


def extract_lighting_info(prompt: str) -> Dict[str, Any]:
    """Extract lighting info from prompt using comprehensive keyword matching."""
    info = {}
    
    info["has_natural_light"] = match_keywords(prompt, LIGHTING_KEYWORDS["natural"])
    info["has_backlight"] = match_keywords(prompt, LIGHTING_KEYWORDS["backlight"])
    info["has_side_light"] = match_keywords(prompt, LIGHTING_KEYWORDS["side"])
    info["has_low_key"] = match_keywords(prompt, LIGHTING_KEYWORDS["low_key"])
    info["has_high_key"] = match_keywords(prompt, LIGHTING_KEYWORDS["high_key"])
    info["has_practical"] = match_keywords(prompt, LIGHTING_KEYWORDS["practical"])
    info["has_motivated"] = match_keywords(prompt, LIGHTING_KEYWORDS["motivated"])
    
    return info


def extract_color_info(prompt: str) -> Dict[str, Any]:
    """Extract color grading info from prompt."""
    info = {}
    
    info["has_warm"] = match_keywords(prompt, COLOR_KEYWORDS["warm"])
    info["has_cool"] = match_keywords(prompt, COLOR_KEYWORDS["cool"])
    info["has_desaturated"] = match_keywords(prompt, COLOR_KEYWORDS["desaturated"])
    info["has_vibrant"] = match_keywords(prompt, COLOR_KEYWORDS["vibrant"])
    
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
