"""Reranker Registry with Auto-discovery.

P4: rerankers/ 디렉토리의 모든 BaseReranker 서브클래스를 자동 발견.

Usage:
    from app.rag.rerankers import get_reranker, list_rerankers

    # 특정 리랭커 가져오기
    reranker = get_reranker("local_cross_encoder")
    result = await reranker.rerank("검색 쿼리", documents)

    # 등록된 모든 리랭커 목록
    rerankers = list_rerankers()  # ["vertex", "local_cross_encoder"]

Available Rerankers:
    - vertex: Vertex AI Ranking API (hosted)
    - local_cross_encoder: Local CrossEncoder (BGE, ms-marco)
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import BaseReranker, RerankResult, DocumentToRerank, RerankerError

logger = logging.getLogger(__name__)

# Registry
_RERANKERS: Dict[str, BaseReranker] = {}
_RERANKER_CLASSES: Dict[str, Type[BaseReranker]] = {}
_discovered = False


def _discover_rerankers() -> None:
    """rerankers/ 디렉토리에서 BaseReranker 서브클래스 자동 발견."""
    global _discovered

    if _discovered:
        return

    reranker_dir = Path(__file__).parent

    for finder, name, ispkg in pkgutil.iter_modules([str(reranker_dir)]):
        # 스킵: __init__, base, 프라이빗 모듈
        if name.startswith("_") or name == "base":
            continue

        try:
            module = importlib.import_module(f".{name}", __package__)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # BaseReranker 서브클래스 찾기
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseReranker)
                    and attr is not BaseReranker
                    and hasattr(attr, "backend_id")
                    and attr.backend_id != "base"
                ):
                    backend_id = attr.backend_id
                    _RERANKER_CLASSES[backend_id] = attr
                    logger.info(
                        f"[RerankerRegistry] Discovered: {backend_id} ({attr.__name__})"
                    )

        except Exception as e:
            logger.warning(f"[RerankerRegistry] Failed to load {name}: {e}")

    logger.info(f"[RerankerRegistry] Total rerankers discovered: {len(_RERANKER_CLASSES)}")
    _discovered = True


def get_reranker(
    backend_id: str,
    *,
    model: Optional[str] = None,
    **kwargs,
) -> Optional[BaseReranker]:
    """리랭커 인스턴스 반환.

    Args:
        backend_id: 리랭커 식별자 ("vertex", "local_cross_encoder")
        model: 모델 오버라이드 (local_cross_encoder: "bge-base", "ms-marco" 등)
        **kwargs: 리랭커 생성자에 전달할 추가 인자

    Returns:
        BaseReranker 인스턴스 또는 None

    Example:
        # Vertex AI Reranker
        reranker = get_reranker("vertex")

        # Local CrossEncoder with specific model
        reranker = get_reranker("local_cross_encoder", model="bge-large")
    """
    _discover_rerankers()

    reranker_class = _RERANKER_CLASSES.get(backend_id)
    if reranker_class is None:
        logger.warning(f"[RerankerRegistry] Reranker not found: {backend_id}")
        return None

    try:
        # Build kwargs
        init_kwargs = dict(kwargs)
        if model is not None:
            init_kwargs["model"] = model

        # Create cache key with model
        cache_key = f"{backend_id}:{model or 'default'}"

        # Return cached instance if exists
        if cache_key in _RERANKERS:
            return _RERANKERS[cache_key]

        # Create new instance
        instance = reranker_class(**init_kwargs)
        _RERANKERS[cache_key] = instance
        logger.debug(f"[RerankerRegistry] Created instance: {cache_key}")
        return instance

    except Exception as e:
        logger.error(f"[RerankerRegistry] Failed to instantiate {backend_id}: {e}")
        return None


def list_rerankers() -> List[str]:
    """등록된 모든 리랭커 ID 목록.

    Returns:
        정렬된 backend_id 목록
    """
    _discover_rerankers()
    return sorted(_RERANKER_CLASSES.keys())


def get_reranker_class(backend_id: str) -> Optional[Type[BaseReranker]]:
    """리랭커 클래스 반환 (인스턴스 아님).

    Args:
        backend_id: 리랭커 식별자

    Returns:
        BaseReranker 서브클래스 또는 None
    """
    _discover_rerankers()
    return _RERANKER_CLASSES.get(backend_id)


def reload_rerankers() -> int:
    """리랭커 레지스트리 리로드 (개발/테스트용).

    Returns:
        발견된 리랭커 수
    """
    global _discovered, _RERANKERS, _RERANKER_CLASSES
    _discovered = False
    _RERANKERS.clear()
    _RERANKER_CLASSES.clear()
    _discover_rerankers()
    return len(_RERANKER_CLASSES)


# Public exports
__all__ = [
    # Base classes
    "BaseReranker",
    "RerankResult",
    "DocumentToRerank",
    "RerankerError",
    # Registry functions
    "get_reranker",
    "list_rerankers",
    "get_reranker_class",
    "reload_rerankers",
]
