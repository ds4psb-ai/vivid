"""
App RAG Registry Service.

앱별 RAG 컨텍스트 검색 및 프롬프트 주입 서비스.
- 멀티 차원 동시 검색
- 히스토리 기반 증폭
- 프롬프트 템플릿 주입

Usage:
    from app.rag import get_app_registry

    registry = get_app_registry()

    # 앱별 컨텍스트 검색
    context = await registry.get_context_for_app(
        app_key="dimension.aesthetic.direct",
        query="bong joon-ho visual style dark mood"
    )

    # 프롬프트에 주입
    enhanced_prompt = registry.inject_context(
        base_prompt="Generate aesthetic guide for...",
        rag_context=context
    )
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.rag.tier1_dimension_rag import get_dimension_rag, Tier1DimensionRAG
from app.rag.app_manifest import (
    APP_MANIFESTS,
    AppRAGManifest,
    get_manifest,
)
# P1: Dataset routing
from app.rag.hybrid_rag import _select_datasets, _apply_dataset_filter

logger = logging.getLogger(__name__)


class AppRAGRegistry:
    """앱별 RAG 컨텍스트 관리 서비스.

    Features:
    - 멀티 차원 병렬 검색
    - 결과 병합 및 중복 제거
    - 프롬프트 템플릿 주입
    - 히스토리 기반 증폭
    """

    def __init__(self):
        """Initialize registry."""
        self._dimension_rags: Dict[str, Tier1DimensionRAG] = {}

    def _get_rag(self, dimension: str) -> Tier1DimensionRAG:
        """차원별 RAG 인스턴스 캐시 조회.

        Args:
            dimension: 차원 ID

        Returns:
            Tier1DimensionRAG instance
        """
        if dimension not in self._dimension_rags:
            self._dimension_rags[dimension] = get_dimension_rag(dimension)
        return self._dimension_rags[dimension]

    def get_context_for_app(
        self,
        app_key: str,
        query: str,
        history_context: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """앱에 대한 RAG 컨텍스트 검색.

        Args:
            app_key: 앱 식별자
            query: 검색 쿼리
            history_context: 이전 단계 히스토리 (증폭용)
            metadata_filters: 추가 필터 조건

        Returns:
            {
                "results": [...],  # 검색 결과
                "dimensions_searched": ["AD", "1D"],
                "total_results": 7,
                "formatted_context": "...",  # 프롬프트 주입용 포맷
            }
        """
        manifest = get_manifest(app_key)
        if not manifest:
            logger.warning(f"No manifest found for app: {app_key}")
            return {
                "results": [],
                "dimensions_searched": [],
                "total_results": 0,
                "formatted_context": "",
            }

        # 증폭: 히스토리 컨텍스트를 쿼리에 추가
        enhanced_query = query
        if manifest.amplify_with_history and history_context:
            enhanced_query = f"{query}\n\nPrevious Context:\n{history_context}"

        # 각 차원에서 동기적으로 검색 (Qdrant 클라이언트가 동기식)
        all_results: List[Dict[str, Any]] = []
        dimensions_searched: List[str] = []

        for dimension in manifest.dimensions:
            try:
                rag = self._get_rag(dimension)

                # 메타데이터 필터 병합
                combined_filters = {
                    **(manifest.metadata_filters or {}),
                    **(metadata_filters or {}),
                }

                # P1: Dataset routing - 선택된 dataset으로 필터
                selected_datasets = _select_datasets(enhanced_query, manifest)
                if selected_datasets:
                    combined_filters = _apply_dataset_filter(combined_filters, selected_datasets)
                    logger.debug(f"[{app_key}] Dataset filter applied: {selected_datasets}")

                # 검색 실행
                results = rag.search(
                    query=enhanced_query,
                    limit=manifest.search_limit,
                    app_key=app_key if combined_filters else None,
                    min_score=manifest.min_score,
                    metadata_filters=combined_filters if combined_filters else None,  # P1: 필터 전달
                )

                for r in results:
                    r["source_dimension"] = dimension

                all_results.extend(results)
                dimensions_searched.append(dimension)
                logger.debug(f"[{app_key}] {dimension}: {len(results)} results")

            except Exception as e:
                logger.error(f"[{app_key}] Failed to search {dimension}: {e}")
                if not manifest.fallback_enabled:
                    raise

        # 점수 기준 정렬 및 중복 제거
        seen_contents = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x.get("score", 0), reverse=True):
            content_hash = hash(r.get("content", "")[:100])
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(r)

        # 포맷된 컨텍스트 생성
        formatted_context = self._format_results(unique_results, manifest)

        return {
            "results": unique_results,
            "dimensions_searched": dimensions_searched,
            "total_results": len(unique_results),
            "formatted_context": formatted_context,
        }

    def _format_results(
        self,
        results: List[Dict[str, Any]],
        manifest: AppRAGManifest,
    ) -> str:
        """검색 결과를 프롬프트 주입용 문자열로 포맷.

        Args:
            results: 검색 결과 리스트
            manifest: 앱 매니페스트

        Returns:
            포맷된 문자열
        """
        if not results:
            return ""

        # P1.5: cross_dataset_template가 있으면 dataset별 그룹화
        if manifest.cross_dataset_template and manifest.dataset_labels:
            return self._format_by_dataset(results, manifest)

        # 기존 로직: 차원별 그룹화
        by_dimension: Dict[str, List[Dict]] = {}
        for r in results:
            dim = r.get("source_dimension", "unknown")
            if dim not in by_dimension:
                by_dimension[dim] = []
            by_dimension[dim].append(r)

        # 포맷 생성
        lines = []
        for dim, items in by_dimension.items():
            lines.append(f"### From {dim} Knowledge Base")
            for i, item in enumerate(items[:5], 1):  # 차원당 최대 5개
                content = item.get("content", "")[:500]  # 최대 500자
                score = item.get("score", 0)
                lines.append(f"{i}. [Score: {score:.2f}] {content}")
            lines.append("")

        rag_results = "\n".join(lines)

        # 템플릿에 주입
        if manifest.prompt_injection_template:
            return manifest.prompt_injection_template.format(rag_results=rag_results)
        return rag_results

    def _format_by_dataset(
        self,
        results: List[Dict[str, Any]],
        manifest: AppRAGManifest,
    ) -> str:
        """P1.5: Dataset별 그룹화 + 라벨링.
        
        Args:
            results: 검색 결과 리스트
            manifest: 앱 매니페스트
            
        Returns:
            cross_dataset_template가 적용된 포맷 문자열
        """
        # Dataset별 그룹화
        by_dataset: Dict[str, List[Dict]] = {}
        for r in results:
            dataset_id = r.get("metadata", {}).get("dataset_id", "unknown")
            if dataset_id not in by_dataset:
                by_dataset[dataset_id] = []
            by_dataset[dataset_id].append(r)
        
        # 각 dataset 섹션 생성
        dataset_sections = []
        for dataset_id, items in by_dataset.items():
            # 라벨 가져오기 (없으면 dataset_id 사용)
            label = manifest.dataset_labels.get(dataset_id, dataset_id)
            
            section_lines = [f"### {label}"]
            for i, item in enumerate(items[:3], 1):  # dataset당 최대 3개
                content = item.get("content", "")[:400]
                score = item.get("score", 0)
                # P1.6 준비: dataset 라벨 포함
                section_lines.append(f"{i}. (dataset={dataset_id}) [Score: {score:.2f}] {content}")
            
            dataset_sections.append("\n".join(section_lines))
        
        # 템플릿에 주입
        datasets_content = "\n\n".join(dataset_sections)
        
        if manifest.cross_dataset_template:
            return manifest.cross_dataset_template.format(datasets=datasets_content)
        return datasets_content

    def inject_context(
        self,
        base_prompt: str,
        rag_context: Dict[str, Any],
        position: str = "prepend",
    ) -> str:
        """RAG 컨텍스트를 프롬프트에 주입.

        Args:
            base_prompt: 원본 프롬프트
            rag_context: get_context_for_app() 반환값
            position: "prepend", "append", "replace_{marker}"

        Returns:
            RAG 컨텍스트가 주입된 프롬프트
        """
        formatted = rag_context.get("formatted_context", "")
        if not formatted:
            return base_prompt

        if position == "prepend":
            return f"{formatted}\n\n{base_prompt}"
        elif position == "append":
            return f"{base_prompt}\n\n{formatted}"
        elif position.startswith("replace_"):
            marker = position.replace("replace_", "")
            return base_prompt.replace(f"{{{marker}}}", formatted)
        else:
            return f"{formatted}\n\n{base_prompt}"

    def register_document(
        self,
        app_key: str,
        doc_id: str,
        content: str,
        dimension: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """앱에 문서 등록 (인덱싱).

        Args:
            app_key: 앱 식별자
            doc_id: 문서 고유 ID
            content: 인덱싱할 콘텐츠
            dimension: 특정 차원 지정 (None이면 매니페스트 첫 번째 차원)
            metadata: 추가 메타데이터

        Returns:
            True if successful
        """
        manifest = get_manifest(app_key)
        if not manifest:
            logger.warning(f"No manifest found for app: {app_key}")
            return False

        # 타겟 차원 결정
        target_dimension = dimension or manifest.dimensions[0]
        if target_dimension not in manifest.dimensions:
            logger.warning(
                f"Dimension {target_dimension} not in manifest for {app_key}"
            )
            target_dimension = manifest.dimensions[0]

        try:
            rag = self._get_rag(target_dimension)

            # 메타데이터에 app_key 추가
            full_metadata = {
                "app_key": app_key,
                "source": "registry",
                **(metadata or {}),
            }

            return rag.index_document(doc_id, content, full_metadata)

        except Exception as e:
            logger.error(f"Failed to register document for {app_key}: {e}")
            return False

    def get_stats(self, app_key: Optional[str] = None) -> Dict[str, Any]:
        """통계 조회.

        Args:
            app_key: 특정 앱만 조회 (None이면 전체)

        Returns:
            통계 딕셔너리
        """
        if app_key:
            manifest = get_manifest(app_key)
            if not manifest:
                return {"error": f"Unknown app: {app_key}"}

            stats = {
                "app_key": app_key,
                "dimensions": manifest.dimensions,
                "dimension_stats": {},
            }
            for dim in manifest.dimensions:
                rag = self._get_rag(dim)
                stats["dimension_stats"][dim] = rag.get_collection_stats()
            return stats

        # 전체 통계
        return {
            "total_apps": len(APP_MANIFESTS),
            "apps": list(APP_MANIFESTS.keys()),
            "dimensions_in_use": list(
                set(
                    dim
                    for m in APP_MANIFESTS.values()
                    for dim in m.dimensions
                )
            ),
        }


# 싱글톤 인스턴스
_registry_instance: Optional[AppRAGRegistry] = None


def get_app_registry() -> AppRAGRegistry:
    """앱 RAG 레지스트리 싱글톤 반환.

    Returns:
        AppRAGRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AppRAGRegistry()
    return _registry_instance


def reset_registry() -> None:
    """레지스트리 리셋 (테스트용)."""
    global _registry_instance
    _registry_instance = None
