"""RAG Suggestion Schema.

P1.6: RAG 추천 UX를 위한 스키마 정의.
- 자동 적용 없이 추천 카드로만 노출
- 근거(evidence_refs) + 신뢰도(confidence) 제공

2025-2026 Best Practices:
- Confidence: 라벨 사용 ("high", "medium", "low") - raw decimals 지양
- Evidence: 소스 어트리뷰션 필수
- Control: 사용자가 거부/수정 가능해야 함
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConfidenceLevel(str, Enum):
    """신뢰도 레벨 (2025 UX 가이드: raw decimal 대신 라벨 사용)."""
    HIGH = "high"      # >= 0.75
    MEDIUM = "medium"  # >= 0.5
    LOW = "low"        # < 0.5


@dataclass
class EvidenceRef:
    """검색 결과의 근거 참조.
    
    Attributes:
        ref_id: 고유 참조 ID (예: "db:rag_docs:AI:psych_core_001")
        source: 소스 타입 (db, sheet, url)
        content_preview: 내용 미리보기 (최대 200자)
        dataset_id: P1 dataset_id
        dataset_label: P1.5 dataset_labels의 human-readable 버전
        score: 검색 점수 (0-1)
    """
    ref_id: str
    source: str = "db"  # "db" | "sheet" | "url"
    content_preview: str = ""
    dataset_id: str = ""
    dataset_label: str = ""
    score: float = 0.0


@dataclass
class PromptChip:
    """Quick insert용 프롬프트 칩.
    
    사용자가 클릭하면 입력창에 삽입됨.
    """
    label: str  # 표시 텍스트
    insert_text: str  # 삽입될 텍스트
    chip_type: str = "keyword"  # "keyword" | "question" | "context"


@dataclass
class RAGSuggestion:
    """RAG 기반 추천 결과.
    
    P1.6: 자동 적용 없이 추천 카드로만 노출됨.
    사용자가 "적용" 클릭 시에만 반영.
    
    Attributes:
        has_suggestion: 추천 결과 유무
        confidence: 신뢰도 (0-1, 내부용)
        confidence_level: 신뢰도 레벨 (UI용)
        evidence_refs: 근거 목록
        prompt_chips: 빠른 삽입 칩
        suggested_context: 전체 추천 컨텍스트 (적용 시 주입)
        datasets_used: 사용된 dataset_id 목록
        total_results: 검색된 총 결과 수
        alternatives: 대안 추천 (향후 확장용)
    """
    has_suggestion: bool = False
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    prompt_chips: List[PromptChip] = field(default_factory=list)
    suggested_context: str = ""
    datasets_used: List[str] = field(default_factory=list)
    total_results: int = 0
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    trace_id: Optional[str] = None  # P6-6: Observability


def calculate_confidence_level(score: float) -> ConfidenceLevel:
    """점수를 신뢰도 레벨로 변환.
    
    2025 UX 가이드: raw decimal 대신 직관적 라벨 사용.
    """
    if score >= 0.75:
        return ConfidenceLevel.HIGH
    elif score >= 0.5:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW


def build_evidence_ref_id(
    dimension: str,
    dataset_id: str,
    doc_id: str,
) -> str:
    """Evidence ref ID 생성.
    
    Format: db:rag_docs:{dimension}:{dataset_id}:{doc_id}
    """
    return f"db:rag_docs:{dimension}:{dataset_id}:{doc_id}"
