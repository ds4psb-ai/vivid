"""RAG Source Registry.

다양한 RAG 소스를 등록하고 관리하는 레지스트리.
런타임 동적 등록/해제 지원 (Composable Pattern).

References:
    - LlamaIndex QueryEngineTool Registry
    - LangChain Tool Registry
"""

from __future__ import annotations

import logging
from typing import Any

from app.rag.router.backends.base import RAGSourceBackend
from app.rag.router.types import (
    RAGSourceSpec,
    RAGSourceType,
    DIMENSION_SOURCE_PRIORITY,
)

logger = logging.getLogger(__name__)


class RAGSourceRegistry:
    """RAG 소스 레지스트리 - Composable Pattern.

    여러 RAG 소스를 등록하고 관리합니다.
    런타임에 동적으로 소스를 추가/제거할 수 있습니다.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._sources: dict[str, RAGSourceSpec] = {}
        self._backends: dict[str, RAGSourceBackend] = {}

    def register(
        self,
        spec: RAGSourceSpec,
        backend: RAGSourceBackend,
    ) -> None:
        """새 RAG 소스 등록.

        Args:
            spec: 소스 명세
            backend: 백엔드 인스턴스
        """
        self._sources[spec.source_id] = spec
        self._backends[spec.source_id] = backend
        logger.info(
            f"[RAGRegistry] Registered source: {spec.source_id} "
            f"({spec.source_type.value})"
        )

    def unregister(self, source_id: str) -> bool:
        """RAG 소스 제거.

        Args:
            source_id: 소스 ID

        Returns:
            True if removed, False if not found
        """
        if source_id in self._sources:
            del self._sources[source_id]
            del self._backends[source_id]
            logger.info(f"[RAGRegistry] Unregistered source: {source_id}")
            return True
        return False

    def get_spec(self, source_id: str) -> RAGSourceSpec | None:
        """소스 명세 조회."""
        return self._sources.get(source_id)

    def get_backend(self, source_id: str) -> RAGSourceBackend | None:
        """백엔드 인스턴스 조회."""
        return self._backends.get(source_id)

    def get_all_sources(self) -> list[RAGSourceSpec]:
        """모든 소스 목록."""
        return list(self._sources.values())

    def get_enabled_sources(self) -> list[RAGSourceSpec]:
        """활성화된 소스 목록."""
        return [s for s in self._sources.values() if s.enabled]

    def get_by_type(self, source_type: RAGSourceType) -> list[RAGSourceSpec]:
        """특정 타입의 소스 목록.

        Args:
            source_type: RAG 소스 타입

        Returns:
            해당 타입의 소스 목록
        """
        return [
            s
            for s in self._sources.values()
            if s.source_type == source_type and s.enabled
        ]

    def get_for_dimension(self, dimension: str) -> list[RAGSourceSpec]:
        """특정 Dimension에 적합한 소스 목록.

        Args:
            dimension: Dimension 코드 (1D, 2D, 3D, 4D, AD, etc.)

        Returns:
            우선순위 정렬된 소스 목록
        """
        # Dimension별 기본 우선순위
        priority_types = DIMENSION_SOURCE_PRIORITY.get(
            dimension,
            [RAGSourceType.MULTIMODAL_DIMENSION, RAGSourceType.AUTEUR_DNA],
        )

        result = []
        for source_type in priority_types:
            result.extend(self.get_by_type(source_type))

        # 나머지 활성 소스 추가 (중복 제외)
        seen_ids = {s.source_id for s in result}
        for source in self.get_enabled_sources():
            if source.source_id not in seen_ids:
                # Dimension 지원 여부 확인
                if (
                    source.supported_dimensions is None
                    or dimension in source.supported_dimensions
                ):
                    result.append(source)

        return result

    def get_source_descriptions(self) -> str:
        """LLM 프롬프트용 소스 설명 생성.

        Returns:
            포맷된 소스 설명 문자열
        """
        lines = []
        for source in self.get_enabled_sources():
            lines.append(
                f"- {source.source_id} ({source.source_type.value}): "
                f"{source.description}"
            )
            if source.keywords:
                lines.append(f"  Keywords: {', '.join(source.keywords)}")
        return "\n".join(lines)

    async def health_check_all(self) -> dict[str, bool]:
        """모든 소스 헬스 체크.

        Returns:
            source_id → health status 맵
        """
        results = {}
        for source_id, backend in self._backends.items():
            try:
                results[source_id] = await backend.health_check()
            except Exception as e:
                logger.error(f"[RAGRegistry] Health check failed: {source_id}: {e}")
                results[source_id] = False
        return results


# =============================================================================
# Global Registry Singleton
# =============================================================================

_global_registry: RAGSourceRegistry | None = None


def get_rag_registry() -> RAGSourceRegistry:
    """전역 RAG 레지스트리 반환 (싱글톤)."""
    global _global_registry
    if _global_registry is None:
        _global_registry = RAGSourceRegistry()
    return _global_registry


def reset_rag_registry() -> None:
    """전역 레지스트리 리셋 (테스트용)."""
    global _global_registry
    _global_registry = None


# =============================================================================
# Default Source Specs
# =============================================================================


def get_default_source_specs() -> list[RAGSourceSpec]:
    """기본 소스 스펙 목록.

    Returns:
        기본 설정된 RAGSourceSpec 리스트
    """
    return [
        RAGSourceSpec(
            source_id="notebooklm",
            source_type=RAGSourceType.AUTEUR_DNA,
            display_name="거장 DNA",
            description="영화 거장들의 스타일, 기법, 철학에 대한 깊이있는 지식",
            keywords=["거장", "스타일", "봉준호", "쿠브릭", "놀란", "auteur"],
            priority=9,
            latency_ms_avg=2000,
            backend_type="notebooklm",
        ),
        RAGSourceSpec(
            source_id="multimodal_qdrant",
            source_type=RAGSourceType.MULTIMODAL_DIMENSION,
            display_name="멀티모달 차원 지식",
            description="차원별(1D-4D, AD) 텍스트, 이미지, 오디오, 비디오 지식",
            keywords=["차원", "dimension", "이미지", "영상", "오디오"],
            priority=8,
            latency_ms_avg=500,
            backend_type="qdrant",
        ),
        RAGSourceSpec(
            source_id="user_history",
            source_type=RAGSourceType.USER_HISTORY,
            display_name="작업 히스토리",
            description="사용자의 과거 작업 결과와 컨텍스트",
            keywords=["이전에", "지난번", "예전", "히스토리", "과거"],
            priority=6,
            latency_ms_avg=200,
            backend_type="postgres",
            requires_auth=True,
        ),
    ]


async def setup_default_registry(
    db_session_factory: Any = None,
) -> RAGSourceRegistry:
    """기본 소스로 레지스트리 설정.

    Args:
        db_session_factory: DB 세션 팩토리 (UserHistory용)

    Returns:
        설정된 레지스트리
    """
    from app.rag.router.backends.notebooklm import (
        NotebookLMBackend,
        MockNotebookLMBackend,
    )
    from app.rag.router.backends.multimodal_qdrant import (
        MultiModalQdrantBackend,
        MockMultiModalQdrantBackend,
    )
    from app.rag.router.backends.user_history import (
        UserHistoryBackend,
        MockUserHistoryBackend,
    )

    registry = get_rag_registry()
    specs = get_default_source_specs()

    for spec in specs:
        backend: RAGSourceBackend

        if spec.source_id == "notebooklm":
            try:
                backend = NotebookLMBackend()
            except Exception:
                backend = MockNotebookLMBackend()

        elif spec.source_id == "multimodal_qdrant":
            try:
                backend = MultiModalQdrantBackend()
            except Exception:
                backend = MockMultiModalQdrantBackend()

        elif spec.source_id == "user_history":
            if db_session_factory:
                backend = UserHistoryBackend(db_session_factory)
            else:
                backend = MockUserHistoryBackend()

        else:
            continue

        registry.register(spec, backend)

    return registry
