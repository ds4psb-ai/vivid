"""RAG Suggestion Service.

P1.6: RAG 검색 결과를 추천 카드 형태로 변환.
- 자동 적용 없이 사용자가 선택/거부 가능
- 근거(evidence) + 신뢰도(confidence) 제공
"""
import logging
from typing import Any, Dict, List, Optional

from app.rag.app_registry import get_app_registry
from app.rag.app_manifest import get_manifest
from app.rag.rag_suggestion import (
    RAGSuggestion,
    EvidenceRef,
    PromptChip,
    ConfidenceLevel,
    calculate_confidence_level,
    build_evidence_ref_id,
)

logger = logging.getLogger(__name__)


class RAGSuggestionService:
    """RAG 기반 추천 서비스.
    
    P1.6: 검색 결과를 추천 카드로 변환.
    """
    
    def __init__(self):
        self._registry = get_app_registry()
    
    def get_suggestion(
        self,
        app_key: str,
        query: str,
        history_context: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> RAGSuggestion:
        """RAG 검색 기반 추천 생성.
        
        Args:
            app_key: 앱 식별자 (예: "dimension.persona.analyze")
            query: 검색 쿼리
            history_context: 이전 단계 히스토리
            inputs: 추가 입력값 (옵션)
            
        Returns:
            RAGSuggestion with confidence and evidence
        """
        manifest = get_manifest(app_key)
        if not manifest:
            logger.warning(f"[SuggestionService] No manifest for: {app_key}")
            return RAGSuggestion(has_suggestion=False)
        
        # RAG 검색 실행
        try:
            rag_result = self._registry.get_context_for_app(
                app_key=app_key,
                query=query,
                history_context=history_context,
            )
        except Exception as e:
            logger.error(f"[SuggestionService] RAG search failed: {e}")
            return RAGSuggestion(has_suggestion=False)
        
        results = rag_result.get("results", [])
        if not results:
            logger.info(f"[SuggestionService] No results for query: {query[:50]}")
            return RAGSuggestion(has_suggestion=False)
        
        # 신뢰도 계산 (최고 점수 기준)
        scores = [r.get("score", 0) for r in results]
        max_score = max(scores) if scores else 0
        avg_score = sum(scores) / len(scores) if scores else 0
        
        confidence = max_score  # 최고 점수 기준
        confidence_level = calculate_confidence_level(confidence)
        
        # 낮은 신뢰도면 빈 추천 반환
        if confidence < 0.5:
            logger.info(f"[SuggestionService] Low confidence ({confidence:.2f}), skipping")
            return RAGSuggestion(
                has_suggestion=False,
                confidence=confidence,
                confidence_level=confidence_level,
            )
        
        # Evidence refs 생성
        evidence_refs = self._build_evidence_refs(results, manifest)
        
        # Prompt chips 생성
        prompt_chips = self._build_prompt_chips(results, manifest)
        
        # 사용된 datasets 추출
        datasets_used = list(set(
            r.get("metadata", {}).get("dataset_id", "unknown")
            for r in results
        ))
        
        logger.info(
            f"[SuggestionService] Suggestion ready | "
            f"confidence={confidence:.2f} ({confidence_level.value}) | "
            f"evidence={len(evidence_refs)} | chips={len(prompt_chips)}"
        )
        
        return RAGSuggestion(
            has_suggestion=True,
            confidence=confidence,
            confidence_level=confidence_level,
            evidence_refs=evidence_refs,
            prompt_chips=prompt_chips,
            suggested_context=rag_result.get("formatted_context", ""),
            datasets_used=datasets_used,
            total_results=len(results),
        )
    
    def _build_evidence_refs(
        self,
        results: List[Dict[str, Any]],
        manifest,
    ) -> List[EvidenceRef]:
        """검색 결과에서 Evidence refs 생성.
        
        P5+ Hardening:
        - ref_id format guaranteed: db:rag_docs:{dim}:{dataset}:{doc_id}
        - score None/NaN protection: defaults to 0.0
        - dataset_label fallback: dataset_id if label missing
        """
        evidence_refs = []
        seen_ref_ids = set()  # Dedup at backend level too
        
        for r in results[:5]:  # 최대 5개
            metadata = r.get("metadata", {})
            doc_id = r.get("doc_id") or metadata.get("doc_id", "unknown")
            dataset_id = metadata.get("dataset_id", "unknown")
            dimension = r.get("source_dimension") or metadata.get("dimension", "unknown")
            
            # P5: Guaranteed ref_id format
            ref_id = build_evidence_ref_id(dimension, dataset_id, doc_id)
            
            # Dedup
            if ref_id in seen_ref_ids:
                continue
            seen_ref_ids.add(ref_id)
            
            # P5: dataset_label fallback
            dataset_label = manifest.dataset_labels.get(dataset_id, dataset_id) if manifest else dataset_id
            
            # Content preview (최대 200자, strip whitespace)
            content = (r.get("content", "") or "")[:200].strip()
            
            # P5: Score validation - protect against None, NaN
            raw_score = r.get("score")
            if raw_score is None or not isinstance(raw_score, (int, float)):
                score = 0.0
            elif raw_score != raw_score:  # NaN check
                score = 0.0
            else:
                score = float(raw_score)
            
            evidence_refs.append(EvidenceRef(
                ref_id=ref_id,
                source="db",
                content_preview=content,
                dataset_id=dataset_id,
                dataset_label=dataset_label,
                score=score,
            ))
        
        # Sort by score descending
        evidence_refs.sort(key=lambda x: x.score, reverse=True)
        
        return evidence_refs
    
    def _build_prompt_chips(
        self,
        results: List[Dict[str, Any]],
        manifest,
    ) -> List[PromptChip]:
        """검색 결과에서 Prompt chips 생성.
        
        Dataset labels + 주요 키워드 기반.
        """
        chips = []
        
        # Dataset labels를 chip으로 변환
        seen_datasets = set()
        for r in results:
            dataset_id = r.get("metadata", {}).get("dataset_id")
            if dataset_id and dataset_id not in seen_datasets:
                label = manifest.dataset_labels.get(dataset_id, dataset_id)
                chips.append(PromptChip(
                    label=label,
                    insert_text=f"{label} 관점에서 ",
                    chip_type="context",
                ))
                seen_datasets.add(dataset_id)
        
        # 상위 결과에서 키워드 추출 (간단 버전)
        if results:
            top_content = results[0].get("content", "")[:100]
            # 첫 문장 또는 짧은 요약
            first_sentence = top_content.split('.')[0][:50]
            if first_sentence:
                chips.append(PromptChip(
                    label=f"'{first_sentence}...'",
                    insert_text=first_sentence,
                    chip_type="keyword",
                ))
        
        return chips[:4]  # 최대 4개


# 싱글톤 인스턴스
_suggestion_service: Optional[RAGSuggestionService] = None


def get_suggestion_service() -> RAGSuggestionService:
    """RAG Suggestion 서비스 싱글톤 반환."""
    global _suggestion_service
    if _suggestion_service is None:
        _suggestion_service = RAGSuggestionService()
    return _suggestion_service
