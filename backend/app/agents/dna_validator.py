"""
DNA Compliance Validator Agent

서사 DNA 정의에 따라 생성된 콘텐츠의 일관성을 검증하고
위반 사항에 대한 개선 제안을 생성합니다.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel

from app.agents.director import NarrativeDNA
from app.config import settings
from app.logging_config import get_logger

logger = get_logger("dna_validator")


# =============================================================================
# Schemas
# =============================================================================

class ViolationType(str, Enum):
    TONE_MISMATCH = "tone_mismatch"
    CHARACTER_INCONSISTENCY = "character_inconsistency"
    THEME_DEVIATION = "theme_deviation"
    VISUAL_STYLE_CONFLICT = "visual_style_conflict"
    FORBIDDEN_ELEMENT = "forbidden_element"


class ComplianceIssue(BaseModel):
    """DNA 위반 이슈"""
    id: str
    type: ViolationType
    severity: str  # 'low', 'medium', 'high'
    field: str  # 위반된 DNA 필드
    expected: str  # 기대값
    actual: str  # 실제값
    location: Optional[str] = None  # 위반 위치 (예: "대사 3번")
    message: str
    suggestion: str


class ComplianceResult(BaseModel):
    """DNA 준수 검사 결과"""
    content_id: str
    is_compliant: bool
    compliance_score: float  # 0-1
    issues: List[ComplianceIssue]
    checked_fields: List[str]
    timestamp: float


class ValidationRequest(BaseModel):
    """검증 요청"""
    content: str  # 검증할 콘텐츠 (대본, 설명 등)
    content_type: str  # 'script', 'dialogue', 'description', 'visual'
    narrative_dna: Dict[str, Any]
    node_id: Optional[str] = None


# =============================================================================
# Tone Analysis
# =============================================================================

TONE_KEYWORDS = {
    "어둡고": ["암울", "그림자", "어둠", "침묵", "고독", "쓸쓸"],
    "축축한": ["비", "빗물", "젖은", "습기", "안개"],
    "밝은": ["햇살", "빛나는", "환한", "밝게", "빛"],
    "유쾌한": ["웃음", "즐거운", "재미있", "유머", "웃긴"],
    "따뜻한": ["온기", "포근", "따스", "다정", "정겨운"],
    "차가운": ["냉정", "싸늘", "냉담", "차갑", "얼음"],
    "역동적": ["빠른", "에너지", "폭발", "움직임", "액션"],
    "서정적": ["서서히", "고요", "잔잔", "흐르는", "그윽"],
    "프리미엄": ["고급", "럭셔리", "세련", "품격", "명품"],
    "냉소적": ["비꼬", "냉소", "조롱", "비웃", "냉담"],
}

CONFLICTING_TONES = {
    "어둡고": ["밝은", "유쾌한"],
    "밝은": ["어둡고", "암울한"],
    "유쾌한": ["우울한", "어두운"],
    "따뜻한": ["차가운", "냉정한"],
    "차가운": ["따뜻한", "포근한"],
}


# =============================================================================
# DNA Validator Agent
# =============================================================================

class DNAValidator:
    """
    서사 DNA 준수 검증 에이전트
    
    생성된 콘텐츠가 정의된 서사 DNA와 일치하는지 검사합니다.
    """
    
    async def check_compliance(
        self,
        content: str,
        content_type: str,
        dna: NarrativeDNA,
        node_id: Optional[str] = None,
    ) -> ComplianceResult:
        """
        콘텐츠의 DNA 준수 여부를 검사합니다.
        """
        logger.info(
            "Checking DNA compliance",
            extra={"content_type": content_type, "content_length": len(content)}
        )
        
        issues: List[ComplianceIssue] = []
        checked_fields: List[str] = []
        
        # 1. 톤 검사
        tone_issues = self._check_tone(content, dna)
        issues.extend(tone_issues)
        checked_fields.append("overall_tone")
        checked_fields.append("allowed_tones")
        checked_fields.append("forbidden_tones")
        
        # 2. 금지 톤 검사
        forbidden_issues = self._check_forbidden(content, dna)
        issues.extend(forbidden_issues)
        
        # 3. 시각 스타일 검사 (설명/비주얼 콘텐츠의 경우)
        if content_type in ["description", "visual"]:
            style_issues = self._check_visual_style(content, dna)
            issues.extend(style_issues)
            checked_fields.append("visual_style")
        
        # 4. 준수 점수 계산
        compliance_score = self._calculate_score(issues)
        
        import time
        result = ComplianceResult(
            content_id=node_id or f"content_{uuid4().hex[:8]}",
            is_compliant=len([i for i in issues if i.severity == "high"]) == 0,
            compliance_score=compliance_score,
            issues=issues,
            checked_fields=checked_fields,
            timestamp=time.time(),
        )
        
        logger.info(
            "Compliance check complete",
            extra={
                "is_compliant": result.is_compliant,
                "score": compliance_score,
                "issue_count": len(issues),
            }
        )
        
        return result
    
    def _check_tone(self, content: str, dna: NarrativeDNA) -> List[ComplianceIssue]:
        """톤 일치 여부 검사"""
        issues = []
        
        # 허용된 톤의 키워드가 있는지 확인
        allowed_tone_found = False
        for tone in dna.allowed_tones:
            if tone in TONE_KEYWORDS:
                for keyword in TONE_KEYWORDS[tone]:
                    if keyword in content:
                        allowed_tone_found = True
                        break
        
        # 충돌하는 톤이 있는지 확인
        for tone in dna.allowed_tones:
            if tone in CONFLICTING_TONES:
                for conflict in CONFLICTING_TONES[tone]:
                    if conflict in TONE_KEYWORDS:
                        for keyword in TONE_KEYWORDS.get(conflict, []):
                            if keyword in content:
                                issues.append(ComplianceIssue(
                                    id=f"issue_{uuid4().hex[:8]}",
                                    type=ViolationType.TONE_MISMATCH,
                                    severity="medium",
                                    field="overall_tone",
                                    expected=dna.overall_tone,
                                    actual=f"'{keyword}' 발견",
                                    message=f"설정된 톤 '{tone}'과 충돌하는 표현 '{keyword}'이 발견되었습니다.",
                                    suggestion=f"'{keyword}'를 '{dna.overall_tone}'에 맞는 표현으로 수정하세요.",
                                ))
        
        return issues
    
    def _check_forbidden(self, content: str, dna: NarrativeDNA) -> List[ComplianceIssue]:
        """금지된 톤 사용 검사"""
        issues = []
        
        for forbidden in dna.forbidden_tones:
            if forbidden in TONE_KEYWORDS:
                for keyword in TONE_KEYWORDS[forbidden]:
                    if keyword in content:
                        issues.append(ComplianceIssue(
                            id=f"issue_{uuid4().hex[:8]}",
                            type=ViolationType.FORBIDDEN_ELEMENT,
                            severity="high",
                            field="forbidden_tones",
                            expected=f"'{forbidden}' 톤 사용 금지",
                            actual=f"'{keyword}' 발견",
                            message=f"금지된 톤 '{forbidden}'의 키워드 '{keyword}'이 사용되었습니다.",
                            suggestion=f"'{keyword}'를 제거하거나 다른 표현으로 대체하세요.",
                        ))
        
        return issues
    
    def _check_visual_style(self, content: str, dna: NarrativeDNA) -> List[ComplianceIssue]:
        """시각 스타일 일관성 검사"""
        issues = []
        
        # 시각 스타일 키워드 추출
        style_keywords = dna.visual_style.lower().split(",")
        style_keywords = [k.strip() for k in style_keywords if k.strip()]
        
        # 콘텐츠에 스타일 관련 언급이 있는지 확인
        mentioned_count = sum(1 for kw in style_keywords if kw in content.lower())
        
        if mentioned_count == 0 and len(content) > 50:
            issues.append(ComplianceIssue(
                id=f"issue_{uuid4().hex[:8]}",
                type=ViolationType.VISUAL_STYLE_CONFLICT,
                severity="low",
                field="visual_style",
                expected=dna.visual_style,
                actual="스타일 미언급",
                message="정의된 시각 스타일이 콘텐츠에 반영되지 않았습니다.",
                suggestion=f"'{dna.visual_style}' 스타일 요소를 추가 반영하세요.",
            ))
        
        return issues
    
    def _calculate_score(self, issues: List[ComplianceIssue]) -> float:
        """이슈에 기반한 준수 점수 계산"""
        if not issues:
            return 1.0
        
        severity_weights = {
            "high": 0.3,
            "medium": 0.1,
            "low": 0.05,
        }
        
        total_penalty = sum(severity_weights.get(i.severity, 0.05) for i in issues)
        score = max(0.0, 1.0 - total_penalty)
        
        return round(score, 2)
    
    async def generate_suggestions(
        self,
        compliance_result: ComplianceResult,
    ) -> List[Dict[str, Any]]:
        """
        DNA 위반에 대한 프로액티브 제안 생성
        """
        suggestions = []
        
        for issue in compliance_result.issues:
            suggestion = {
                "id": f"sug_{uuid4().hex[:8]}",
                "type": "dna_violation",
                "title": f"{issue.type.value} 감지",
                "message": issue.message,
                "targetNodeId": compliance_result.content_id,
                "suggestedAction": {
                    "type": "fix_tone",
                    "params": {
                        "field": issue.field,
                        "suggestion": issue.suggestion,
                    },
                    "label": "수정하기",
                },
                "confidence": 0.9 if issue.severity == "high" else 0.7,
                "dnaField": issue.field,
                "timestamp": compliance_result.timestamp,
            }
            suggestions.append(suggestion)
        
        return suggestions


# Singleton instance
dna_validator = DNAValidator()
