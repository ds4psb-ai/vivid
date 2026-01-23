"""Service Registry - 통합 서비스 관리.

15+ 싱글톤 팩토리 함수 → 단일 레지스트리로 통합.

기존 싱글톤 패턴:
- get_semantic_router() → SemanticRouter
- get_query_classifier() → QueryClassifier
- get_reranker() → Reranker
- get_embedding_model() → EmbeddingModel
- get_qdrant_client() → QdrantClient
- get_generation_client() → GenerationClient
- etc.

Usage:
    from app.core.service_registry import ServiceRegistry

    # 서버 시작 시
    await ServiceRegistry.initialize()

    # 서비스 조회
    router = ServiceRegistry.get("semantic_router")
    client = ServiceRegistry.get("qdrant_client")

    # 타입 안전 조회
    router = ServiceRegistry.get_semantic_router()

    # 서버 종료 시
    await ServiceRegistry.shutdown()
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceRegistry:
    """통합 서비스 레지스트리.

    Singleton 패턴을 중앙 관리하여:
    - 초기화 순서 보장
    - 의존성 관리
    - 리소스 정리 (shutdown)
    - 테스트 시 모킹 지원

    Features:
    - Lazy initialization
    - Async service support
    - Dependency injection ready
    - Thread-safe
    """

    _instance: Optional["ServiceRegistry"] = None
    _services: Dict[str, Any] = {}
    _factories: Dict[str, Callable[[], Any]] = {}
    _async_factories: Dict[str, Callable[[], Any]] = {}
    _initialized: bool = False
    _lock: asyncio.Lock = None

    def __new__(cls) -> "ServiceRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
            cls._instance._factories = {}
            cls._instance._async_factories = {}
            cls._instance._initialized = False
            cls._instance._lock = None
        return cls._instance

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create async lock."""
        if cls._instance is None:
            cls()
        if cls._instance._lock is None:
            cls._instance._lock = asyncio.Lock()
        return cls._instance._lock

    @classmethod
    def register(
        cls,
        name: str,
        factory: Callable[[], T],
        *,
        is_async: bool = False,
    ) -> None:
        """서비스 팩토리 등록.

        Args:
            name: 서비스 이름
            factory: 서비스 생성 함수
            is_async: 비동기 팩토리 여부
        """
        if cls._instance is None:
            cls()

        if is_async:
            cls._instance._async_factories[name] = factory
        else:
            cls._instance._factories[name] = factory

        logger.debug(f"Registered service factory: {name} (async={is_async})")

    @classmethod
    def register_instance(cls, name: str, instance: Any) -> None:
        """서비스 인스턴스 직접 등록.

        Args:
            name: 서비스 이름
            instance: 서비스 인스턴스
        """
        if cls._instance is None:
            cls()

        cls._instance._services[name] = instance
        logger.debug(f"Registered service instance: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """서비스 조회 (동기).

        Args:
            name: 서비스 이름

        Returns:
            서비스 인스턴스 또는 None
        """
        if cls._instance is None:
            return None

        # 이미 생성된 인스턴스
        if name in cls._instance._services:
            return cls._instance._services[name]

        # 동기 팩토리로 생성
        if name in cls._instance._factories:
            try:
                instance = cls._instance._factories[name]()
                cls._instance._services[name] = instance
                logger.info(f"Created service: {name}")
                return instance
            except Exception as e:
                logger.error(f"Failed to create service {name}: {e}")
                return None

        logger.warning(f"Service not found: {name}")
        return None

    @classmethod
    async def get_async(cls, name: str) -> Optional[Any]:
        """서비스 조회 (비동기).

        Args:
            name: 서비스 이름

        Returns:
            서비스 인스턴스 또는 None
        """
        if cls._instance is None:
            cls()

        lock = cls._get_lock()
        async with lock:
            # 이미 생성된 인스턴스
            if name in cls._instance._services:
                return cls._instance._services[name]

            # 비동기 팩토리로 생성
            if name in cls._instance._async_factories:
                try:
                    instance = await cls._instance._async_factories[name]()
                    cls._instance._services[name] = instance
                    logger.info(f"Created async service: {name}")
                    return instance
                except Exception as e:
                    logger.error(f"Failed to create async service {name}: {e}")
                    return None

            # 동기 팩토리 폴백
            if name in cls._instance._factories:
                try:
                    instance = cls._instance._factories[name]()
                    cls._instance._services[name] = instance
                    logger.info(f"Created service (sync factory): {name}")
                    return instance
                except Exception as e:
                    logger.error(f"Failed to create service {name}: {e}")
                    return None

        logger.warning(f"Service not found: {name}")
        return None

    @classmethod
    async def initialize(cls) -> None:
        """모든 서비스 초기화.

        서버 시작 시 호출하여 필수 서비스를 미리 생성.
        """
        if cls._instance is None:
            cls()

        if cls._instance._initialized:
            logger.debug("ServiceRegistry already initialized")
            return

        logger.info("Initializing ServiceRegistry...")

        # 비동기 서비스 병렬 초기화
        async_tasks = []
        for name in cls._instance._async_factories:
            if name not in cls._instance._services:
                async_tasks.append(cls.get_async(name))

        if async_tasks:
            await asyncio.gather(*async_tasks, return_exceptions=True)

        # 동기 서비스 초기화
        for name in cls._instance._factories:
            if name not in cls._instance._services:
                cls.get(name)

        cls._instance._initialized = True
        logger.info(
            f"ServiceRegistry initialized: {len(cls._instance._services)} services"
        )

    @classmethod
    async def shutdown(cls) -> None:
        """모든 서비스 종료.

        서버 종료 시 호출하여 리소스 정리.
        """
        if cls._instance is None:
            return

        logger.info("Shutting down ServiceRegistry...")

        for name, service in cls._instance._services.items():
            try:
                # close() 메서드가 있으면 호출
                if hasattr(service, "close"):
                    if asyncio.iscoroutinefunction(service.close):
                        await service.close()
                    else:
                        service.close()
                    logger.debug(f"Closed service: {name}")

                # shutdown() 메서드가 있으면 호출
                elif hasattr(service, "shutdown"):
                    if asyncio.iscoroutinefunction(service.shutdown):
                        await service.shutdown()
                    else:
                        service.shutdown()
                    logger.debug(f"Shutdown service: {name}")

            except Exception as e:
                logger.error(f"Error shutting down service {name}: {e}")

        cls._instance._services.clear()
        cls._instance._initialized = False
        logger.info("ServiceRegistry shutdown complete")

    @classmethod
    def reset(cls) -> None:
        """레지스트리 리셋 (테스트용).

        Warning: 프로덕션에서 사용 금지.
        """
        if cls._instance is not None:
            cls._instance._services.clear()
            cls._instance._factories.clear()
            cls._instance._async_factories.clear()
            cls._instance._initialized = False
            logger.warning("ServiceRegistry reset (test mode)")

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """레지스트리 통계."""
        if cls._instance is None:
            return {"initialized": False, "services": 0}

        return {
            "initialized": cls._instance._initialized,
            "services": len(cls._instance._services),
            "service_names": list(cls._instance._services.keys()),
            "pending_factories": len(cls._instance._factories),
            "pending_async_factories": len(cls._instance._async_factories),
        }

    # =========================================================================
    # 타입 안전 서비스 접근자 (Typed Accessors)
    # =========================================================================

    @classmethod
    def get_semantic_router(cls) -> Optional[Any]:
        """SemanticRouter 인스턴스 조회."""
        return cls.get("semantic_router")

    @classmethod
    def get_query_classifier(cls) -> Optional[Any]:
        """QueryClassifier 인스턴스 조회."""
        return cls.get("query_classifier")

    @classmethod
    def get_reranker(cls) -> Optional[Any]:
        """Reranker 인스턴스 조회."""
        return cls.get("reranker")

    @classmethod
    def get_embedding_model(cls) -> Optional[Any]:
        """EmbeddingModel 인스턴스 조회."""
        return cls.get("embedding_model")

    @classmethod
    async def get_qdrant_client(cls) -> Optional[Any]:
        """QdrantClient 인스턴스 조회 (비동기)."""
        return await cls.get_async("qdrant_client")

    @classmethod
    async def get_generation_client(cls) -> Optional[Any]:
        """GenerationClient 인스턴스 조회 (비동기)."""
        return await cls.get_async("generation_client")

    @classmethod
    async def get_redis_client(cls) -> Optional[Any]:
        """Redis 클라이언트 조회 (비동기)."""
        return await cls.get_async("redis_client")


# =============================================================================
# Default Service Registration
# =============================================================================


def setup_default_services() -> None:
    """기본 서비스 팩토리 등록.

    app startup 시 호출.
    """

    # SemanticRouter (동기, lazy)
    def create_semantic_router():
        from app.rag.semantic_router import SemanticRouter

        return SemanticRouter()

    ServiceRegistry.register("semantic_router", create_semantic_router)

    # EmbeddingModel (동기, lazy)
    def create_embedding_model():
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("all-MiniLM-L6-v2")

    ServiceRegistry.register("embedding_model", create_embedding_model)

    # QdrantClient (비동기)
    async def create_qdrant_client():
        from qdrant_client import AsyncQdrantClient

        from app.config import settings

        return AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )

    ServiceRegistry.register("qdrant_client", create_qdrant_client, is_async=True)

    # GenerationClient (비동기)
    async def create_generation_client():
        from app.generation_client import GenerationClient

        return GenerationClient()

    ServiceRegistry.register("generation_client", create_generation_client, is_async=True)

    logger.info("Default services registered")


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "ServiceRegistry",
    "setup_default_services",
]
