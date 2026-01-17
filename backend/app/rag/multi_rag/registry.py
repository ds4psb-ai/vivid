"""RAG Source Registry (P0 2026).

RAG 소스의 동적 등록/해제 및 조회를 관리하는 레지스트리.

Features:
    - 런타임 동적 등록/해제
    - 타입별, 차원별, 거장별 필터링
    - 헬스 체크 및 자동 비활성화
    - 스레드 안전 (asyncio.Lock)

Reference:
    - Composable Pattern: https://www.patterns.dev/posts/composable
    - Registry Pattern: https://martinfowler.com/eaaCatalog/registry.html

Usage:
    from app.rag.multi_rag.registry import get_registry

    registry = get_registry()

    # Register
    registry.register(spec, backend)

    # Query
    sources = registry.get_by_type(RAGSourceType.AUTEUR_DNA)
    sources = registry.get_by_dimension("4D")

    # Health check
    healthy = await registry.check_health("notebooklm_bong")
"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Set

from app.rag.multi_rag.types import (
    RAGSourceBackend,
    RAGSourceSpec,
    RAGSourceType,
)

logger = logging.getLogger(__name__)


class RAGSourceRegistry:
    """RAG 소스 레지스트리.

    Composable Pattern으로 RAG 소스를 동적으로 관리합니다.

    Attributes:
        _sources: 소스 ID -> RAGSourceSpec 매핑
        _backends: 소스 ID -> RAGSourceBackend 매핑
        _lock: asyncio Lock (동시성 제어)

    Thread Safety:
        모든 mutation 작업은 asyncio.Lock으로 보호됩니다.
        읽기 작업은 스냅샷을 반환하여 안전합니다.
    """

    def __init__(self) -> None:
        """레지스트리 초기화."""
        self._sources: Dict[str, RAGSourceSpec] = {}
        self._backends: Dict[str, RAGSourceBackend] = {}
        self._lock = asyncio.Lock()
        self._unhealthy_sources: Set[str] = set()

    # =========================================================================
    # Registration
    # =========================================================================

    async def register(
        self,
        spec: RAGSourceSpec,
        backend: RAGSourceBackend,
    ) -> None:
        """새 RAG 소스 등록.

        Args:
            spec: RAG 소스 명세
            backend: RAG 백엔드 구현체

        Raises:
            ValueError: 이미 존재하는 source_id인 경우

        Example:
            >>> await registry.register(
            ...     RAGSourceSpec(
            ...         source_id="notebooklm_bong",
            ...         source_type=RAGSourceType.AUTEUR_DNA,
            ...         ...
            ...     ),
            ...     notebooklm_backend,
            ... )
        """
        async with self._lock:
            if spec.source_id in self._sources:
                raise ValueError(f"Source already registered: {spec.source_id}")

            self._sources[spec.source_id] = spec
            self._backends[spec.source_id] = backend

            logger.info(
                f"[RAGRegistry] Registered source: {spec.source_id} | "
                f"type={spec.source_type.value} | "
                f"backend={spec.backend_type}"
            )

    def register_sync(
        self,
        spec: RAGSourceSpec,
        backend: RAGSourceBackend,
    ) -> None:
        """동기 버전 등록 (초기화 시 사용).

        Note:
            서버 시작 시 초기화에만 사용하세요.
            런타임에는 async register()를 사용하세요.
        """
        if spec.source_id in self._sources:
            logger.warning(f"[RAGRegistry] Overwriting source: {spec.source_id}")

        self._sources[spec.source_id] = spec
        self._backends[spec.source_id] = backend

        logger.info(
            f"[RAGRegistry] Registered (sync): {spec.source_id} | "
            f"type={spec.source_type.value}"
        )

    async def unregister(self, source_id: str) -> bool:
        """RAG 소스 제거.

        Args:
            source_id: 제거할 소스 ID

        Returns:
            True if removed, False if not found
        """
        async with self._lock:
            if source_id not in self._sources:
                return False

            del self._sources[source_id]
            del self._backends[source_id]
            self._unhealthy_sources.discard(source_id)

            logger.info(f"[RAGRegistry] Unregistered source: {source_id}")
            return True

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_spec(self, source_id: str) -> Optional[RAGSourceSpec]:
        """소스 명세 조회.

        Args:
            source_id: 소스 ID

        Returns:
            RAGSourceSpec or None
        """
        return self._sources.get(source_id)

    def get_backend(self, source_id: str) -> Optional[RAGSourceBackend]:
        """백엔드 인스턴스 조회.

        Args:
            source_id: 소스 ID

        Returns:
            RAGSourceBackend or None
        """
        return self._backends.get(source_id)

    def get_enabled_sources(self) -> List[RAGSourceSpec]:
        """활성화된 소스 목록 (스냅샷).

        Returns:
            활성화된 RAGSourceSpec 리스트 (priority 내림차순)
        """
        return sorted(
            [s for s in self._sources.values() if s.enabled],
            key=lambda s: -s.priority,
        )

    def get_healthy_sources(self) -> List[RAGSourceSpec]:
        """건강한 소스 목록 (enabled + healthy).

        Returns:
            활성화되고 건강한 RAGSourceSpec 리스트
        """
        return [
            s for s in self.get_enabled_sources()
            if s.source_id not in self._unhealthy_sources
        ]

    def get_by_type(self, source_type: RAGSourceType) -> List[RAGSourceSpec]:
        """타입별 소스 조회.

        Args:
            source_type: RAGSourceType enum

        Returns:
            해당 타입의 활성화된 소스 리스트
        """
        return [
            s for s in self.get_enabled_sources()
            if s.source_type == source_type
        ]

    def get_by_dimension(self, dimension: str) -> List[RAGSourceSpec]:
        """차원별 소스 조회.

        Args:
            dimension: 차원 코드 (예: "4D", "AD")

        Returns:
            해당 차원과 연관된 소스 리스트
        """
        dimension_upper = dimension.upper()
        return [
            s for s in self.get_enabled_sources()
            if not s.dimensions or dimension_upper in [d.upper() for d in s.dimensions]
        ]

    def get_by_auteur(self, auteur_key: str) -> List[RAGSourceSpec]:
        """거장별 소스 조회.

        Args:
            auteur_key: 거장 키 (예: "bong", "nolan")

        Returns:
            해당 거장과 연관된 소스 리스트
        """
        auteur_lower = auteur_key.lower()
        return [
            s for s in self.get_enabled_sources()
            if not s.auteur_keys or auteur_lower in [a.lower() for a in s.auteur_keys]
        ]

    def get_all_source_ids(self) -> List[str]:
        """모든 소스 ID 목록.

        Returns:
            등록된 모든 소스 ID 리스트
        """
        return list(self._sources.keys())

    # =========================================================================
    # Health Check
    # =========================================================================

    async def check_health(self, source_id: str) -> bool:
        """단일 소스 헬스 체크.

        Args:
            source_id: 소스 ID

        Returns:
            True if healthy, False otherwise
        """
        backend = self._backends.get(source_id)
        if not backend:
            return False

        try:
            is_healthy = await backend.health_check()

            async with self._lock:
                if is_healthy:
                    self._unhealthy_sources.discard(source_id)
                else:
                    self._unhealthy_sources.add(source_id)

            return is_healthy

        except Exception as e:
            logger.warning(f"[RAGRegistry] Health check failed for {source_id}: {e}")
            async with self._lock:
                self._unhealthy_sources.add(source_id)
            return False

    async def check_all_health(self) -> Dict[str, bool]:
        """모든 소스 헬스 체크 (병렬).

        Returns:
            source_id -> is_healthy 매핑
        """
        tasks = {
            source_id: self.check_health(source_id)
            for source_id in self._sources.keys()
        }

        results = {}
        for source_id, task in tasks.items():
            try:
                results[source_id] = await task
            except Exception:
                results[source_id] = False

        logger.info(
            f"[RAGRegistry] Health check completed: "
            f"{sum(results.values())}/{len(results)} healthy"
        )

        return results

    # =========================================================================
    # Utility
    # =========================================================================

    def __len__(self) -> int:
        """등록된 소스 수."""
        return len(self._sources)

    def __contains__(self, source_id: str) -> bool:
        """소스 존재 여부."""
        return source_id in self._sources

    def stats(self) -> Dict[str, int]:
        """레지스트리 통계.

        Returns:
            type별 소스 수 통계
        """
        stats: Dict[str, int] = {
            "total": len(self._sources),
            "enabled": len(self.get_enabled_sources()),
            "healthy": len(self.get_healthy_sources()),
            "unhealthy": len(self._unhealthy_sources),
        }

        for source_type in RAGSourceType:
            stats[f"type_{source_type.value}"] = len(self.get_by_type(source_type))

        return stats


# =============================================================================
# Singleton Instance
# =============================================================================

_registry: Optional[RAGSourceRegistry] = None


def get_registry() -> RAGSourceRegistry:
    """글로벌 레지스트리 싱글톤 반환.

    Returns:
        RAGSourceRegistry 인스턴스
    """
    global _registry
    if _registry is None:
        _registry = RAGSourceRegistry()
    return _registry


def reset_registry() -> None:
    """레지스트리 리셋 (테스트용).

    Warning:
        테스트 환경에서만 사용하세요.
    """
    global _registry
    _registry = None
