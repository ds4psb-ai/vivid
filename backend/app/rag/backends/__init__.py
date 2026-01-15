"""Backend Registry with Auto-discovery.

backends/ 디렉토리의 모든 BaseBackend 서브클래스를 자동 발견.

Usage:
    from app.rag.backends import get_backend, list_backends

    # 특정 백엔드 가져오기
    backend = get_backend("qdrant_hybrid")
    results = await backend.retrieve("검색 쿼리")

    # 등록된 모든 백엔드 목록
    backends = list_backends()  # ["qdrant_hybrid", "notebooklm", ...]
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import BaseBackend, RetrievalResult

logger = logging.getLogger(__name__)

# Registry
_BACKENDS: Dict[str, BaseBackend] = {}
_BACKEND_CLASSES: Dict[str, Type[BaseBackend]] = {}
_discovered = False


def _discover_backends() -> None:
    """backends/ 디렉토리에서 BaseBackend 서브클래스 자동 발견."""
    global _discovered

    if _discovered:
        return

    backend_dir = Path(__file__).parent

    for finder, name, ispkg in pkgutil.iter_modules([str(backend_dir)]):
        # 스킵: __init__, base, 프라이빗 모듈
        if name.startswith("_") or name == "base":
            continue

        try:
            module = importlib.import_module(f".{name}", __package__)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # BaseBackend 서브클래스 찾기
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseBackend)
                    and attr is not BaseBackend
                    and attr.backend_id  # backend_id가 설정된 것만
                ):
                    backend_id = attr.backend_id
                    _BACKEND_CLASSES[backend_id] = attr
                    logger.info(f"[BackendRegistry] Discovered: {backend_id} ({attr.__name__})")

        except Exception as e:
            logger.warning(f"[BackendRegistry] Failed to load {name}: {e}")

    logger.info(f"[BackendRegistry] Total backends discovered: {len(_BACKEND_CLASSES)}")
    _discovered = True


def get_backend(backend_id: str) -> Optional[BaseBackend]:
    """백엔드 인스턴스 반환 (싱글톤).

    Args:
        backend_id: 백엔드 식별자

    Returns:
        BaseBackend 인스턴스 또는 None
    """
    _discover_backends()

    # 캐시된 인스턴스 반환
    if backend_id in _BACKENDS:
        return _BACKENDS[backend_id]

    # 새 인스턴스 생성
    backend_class = _BACKEND_CLASSES.get(backend_id)
    if backend_class is None:
        logger.warning(f"[BackendRegistry] Backend not found: {backend_id}")
        return None

    try:
        instance = backend_class()
        _BACKENDS[backend_id] = instance
        logger.debug(f"[BackendRegistry] Created instance: {backend_id}")
        return instance
    except Exception as e:
        logger.error(f"[BackendRegistry] Failed to instantiate {backend_id}: {e}")
        return None


def list_backends() -> List[str]:
    """등록된 모든 백엔드 ID 목록.

    Returns:
        정렬된 backend_id 목록
    """
    _discover_backends()
    return sorted(_BACKEND_CLASSES.keys())


def get_backend_class(backend_id: str) -> Optional[Type[BaseBackend]]:
    """백엔드 클래스 반환 (인스턴스 아님).

    Args:
        backend_id: 백엔드 식별자

    Returns:
        BaseBackend 서브클래스 또는 None
    """
    _discover_backends()
    return _BACKEND_CLASSES.get(backend_id)


def reload_backends() -> int:
    """백엔드 레지스트리 리로드 (개발/테스트용).

    Returns:
        발견된 백엔드 수
    """
    global _discovered, _BACKENDS, _BACKEND_CLASSES
    _discovered = False
    _BACKENDS.clear()
    _BACKEND_CLASSES.clear()
    _discover_backends()
    return len(_BACKEND_CLASSES)


# Public exports
__all__ = [
    "BaseBackend",
    "RetrievalResult",
    "get_backend",
    "list_backends",
    "get_backend_class",
    "reload_backends",
]
