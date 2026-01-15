# P2: Backend ABC + Auto-discovery 상세 구현 계획

> **작성일**: 2026-01-15 | **예상 소요**: 3-4시간 | **우선순위**: P2
> **선행 작업**: P0 (Qdrant Native Sparse), P0.5 (Hybrid 컬렉션 마이그레이션), P1 (YAML Manifest)

---

## 1. 현재 상태 분석

### 1.1 완료된 작업
| Phase | 완료 내용 | 커밋 |
|-------|----------|------|
| P0 | Qdrant Native Sparse Vector 활성화 | `0128b669` |
| P0.5 | 전체 10개 Dimension 컬렉션 Hybrid 마이그레이션 | `9af9f182` |
| P1 | YAML Manifest 도입 (`manifest_loader.py`, 12개 YAML) | `ad6250e6` |

### 1.2 현재 RAG 아키텍처
```
┌─────────────────────────────────────────────────────────────┐
│                    현재 Vivid RAG 구현                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ manifest_loader │───▶│  hybrid_rag.py  │                 │
│  │   (YAML 설정)   │    │  (오케스트레이터) │                 │
│  └─────────────────┘    └────────┬────────┘                 │
│                                  │                           │
│            ┌─────────────────────┼─────────────────────┐     │
│            ▼                     ▼                     ▼     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │tier1_dimension  │  │tier0_notebooklm │  │tier0_vertex │  │
│  │(Qdrant Hybrid)  │  │  (거장 DNA)      │  │ (Grounding) │  │
│  │ Dense + Sparse  │  │                 │  │             │  │
│  │ + RRF (Native)  │  │                 │  │             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│                                                             │
│  문제점:                                                     │
│  - 백엔드 하드코딩 (추가 시 코드 수정 필요)                     │
│  - 통일된 인터페이스 부재                                      │
│  - 백엔드 조합 변경 어려움                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 관련 파일 현황
| 파일 | LOC | 역할 | P2 변환 대상 |
|------|-----|------|-------------|
| `tier1_dimension_rag.py` | 590 | Qdrant Dense + Sparse Hybrid | `QdrantHybridBackend` |
| `tier0_notebooklm.py` | 500+ | NotebookLM 거장 DNA | `NotebookLMBackend` |
| `tier0_vertex_rag.py` | 400+ | Vertex AI + Google Grounding | `VertexGroundingBackend` |
| `bm25_search.py` | 408 | Application-level BM25 (deprecated) | 삭제 후보 |
| `sparse/fastembed_sparse.py` | 136 | Qdrant/bm25 Sparse Embedder | 유지 (tier1에서 사용) |

---

## 2. P2 목표

### 2.1 핵심 원칙
> **"백엔드 추가 = Python 파일 1개"** (오케스트레이터 수정 0)

### 2.2 목표 아키텍처
```
┌─────────────────────────────────────────────────────────────┐
│                    P2 목표 아키텍처                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ manifest_loader │───▶│  hybrid_rag.py  │                 │
│  │ (YAML + backends│    │ (Ensemble 호출)  │                 │
│  │  설정 포함)      │    └────────┬────────┘                 │
│  └─────────────────┘             │                          │
│                                  ▼                          │
│                     ┌────────────────────────┐              │
│                     │   Backend Registry     │              │
│                     │   (Auto-discovery)     │              │
│                     └────────────┬───────────┘              │
│                                  │                          │
│      ┌───────────────┬───────────┼───────────┬──────────┐   │
│      ▼               ▼           ▼           ▼          ▼   │
│  ┌────────┐    ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌───┐  │
│  │Qdrant  │    │NotebookLM│ │ Vertex   │ │ 새백엔드│ │...│  │
│  │Hybrid  │    │ Backend  │ │Grounding │ │(미래)  │ │   │  │
│  │Backend │    │          │ │ Backend  │ │        │ │   │  │
│  └────────┘    └──────────┘ └──────────┘ └─────────┘ └───┘  │
│       │              │            │                         │
│       └──────────────┴────────────┘                         │
│                      ▼                                      │
│              ┌───────────────┐                              │
│              │ BaseBackend   │ (ABC)                        │
│              │ - retrieve()  │                              │
│              │ - health_check│                              │
│              └───────────────┘                              │
│                                                             │
│  이점:                                                       │
│  - 백엔드 추가 = backends/new_backend.py 1개                 │
│  - 통일된 RetrievalResult 인터페이스                          │
│  - YAML에서 백엔드 조합 설정 가능                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 디렉토리 구조

```
backend/app/rag/
├── backends/                          # NEW: Backend 플러그인
│   ├── __init__.py                    # Auto-discovery + Registry
│   ├── base.py                        # BaseBackend ABC + RetrievalResult
│   ├── qdrant_hybrid.py               # Qdrant Dense + Sparse (tier1 래핑)
│   ├── notebooklm.py                  # NotebookLM (tier0 래핑)
│   └── vertex_grounding.py            # Vertex AI + Google Search (tier0 래핑)
│
├── manifests/                         # P1에서 완료
│   ├── _schema.yaml
│   └── *.yaml                         # 12개 앱 설정
│
├── manifest_loader.py                 # P1에서 완료 (backends 필드 추가 필요)
├── hybrid_rag.py                      # 오케스트레이터 (Backend Registry 사용)
├── tier1_dimension_rag.py             # 유지 (QdrantHybridBackend에서 래핑)
├── tier0_notebooklm.py                # 유지 (NotebookLMBackend에서 래핑)
├── tier0_vertex_rag.py                # 유지 (VertexGroundingBackend에서 래핑)
└── sparse/                            # 유지
    ├── __init__.py
    └── fastembed_sparse.py
```

---

## 4. 코드 패턴 상세

### 4.1 BaseBackend ABC

```python
# backends/base.py
"""RAG Backend Abstract Base Class.

모든 RAG 백엔드가 구현해야 하는 인터페이스 정의.

Usage:
    from app.rag.backends import BaseBackend, RetrievalResult

    class MyBackend(BaseBackend):
        backend_id = "my_backend"

        async def retrieve(self, query, limit, filters, config):
            ...
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RetrievalResult:
    """통합 검색 결과.

    모든 백엔드에서 반환하는 표준 결과 형식.

    Attributes:
        doc_id: 문서 고유 ID
        text: 문서 텍스트 (또는 요약)
        score: 관련성 점수 (0.0 ~ 1.0, 백엔드별 정규화)
        source: 백엔드 ID (예: "qdrant_hybrid", "notebooklm")
        rank: 해당 백엔드 내 순위 (1부터 시작)
        metadata: 추가 메타데이터 (dimension, app_key 등)
    """
    doc_id: str
    text: str
    score: float
    source: str
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseBackend(ABC):
    """RAG 백엔드 기본 인터페이스.

    모든 백엔드 구현체는 이 클래스를 상속해야 합니다.

    Class Attributes:
        backend_id: 고유 백엔드 식별자 (예: "qdrant_hybrid", "notebooklm")
                    YAML manifest의 backends[].id와 매칭됨
    """

    backend_id: str = ""  # 서브클래스에서 오버라이드

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """검색 실행.

        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            filters: 메타데이터 필터 (app_key, dataset_id 등)
            config: 백엔드별 추가 설정 (dimension, collection 등)

        Returns:
            RetrievalResult 리스트 (score 내림차순)
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """백엔드 상태 확인.

        Returns:
            True if healthy, False otherwise
        """
        pass

    async def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """문서 인덱싱 (선택적 구현).

        인덱싱을 지원하지 않는 백엔드는 False 반환.

        Args:
            doc_id: 문서 ID
            text: 문서 텍스트
            metadata: 추가 메타데이터

        Returns:
            True if successful, False if not supported or failed
        """
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(backend_id='{self.backend_id}')>"
```

### 4.2 Backend Registry (Auto-discovery)

```python
# backends/__init__.py
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
```

### 4.3 QdrantHybridBackend

```python
# backends/qdrant_hybrid.py
"""Qdrant Hybrid Search Backend.

Qdrant Native Dense + Sparse + RRF Fusion.
tier1_dimension_rag.py의 hybrid_search()를 래핑.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseBackend, RetrievalResult

logger = logging.getLogger(__name__)


class QdrantHybridBackend(BaseBackend):
    """Qdrant Dense + Sparse Hybrid Search Backend.

    Features:
    - Dense vector search (all-MiniLM-L6-v2)
    - Sparse vector search (Qdrant/bm25 + Server-side IDF)
    - RRF Fusion (Qdrant Native)
    - Dimension별 컬렉션 자동 선택
    """

    backend_id = "qdrant_hybrid"

    def __init__(self):
        self._rag_cache: Dict[str, "Tier1DimensionRAG"] = {}

    def _get_rag(self, dimension: str) -> "Tier1DimensionRAG":
        """차원별 RAG 인스턴스 (캐시)."""
        if dimension not in self._rag_cache:
            from app.rag.tier1_dimension_rag import get_dimension_rag
            self._rag_cache[dimension] = get_dimension_rag(dimension)
        return self._rag_cache[dimension]

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """Qdrant Hybrid Search 실행.

        Config options:
            dimension: 차원 코드 (1D, AD, VEO 등) - 필수
            prefetch_limit: Dense/Sparse 각각의 prefetch 수 (기본: 20)
            min_score: 최소 점수 (기본: 0.0)
        """
        config = config or {}
        filters = filters or {}

        dimension = config.get("dimension", "1D")
        prefetch_limit = config.get("prefetch_limit", 20)
        min_score = config.get("min_score", 0.0)

        rag = self._get_rag(dimension)

        try:
            results = rag.hybrid_search(
                query=query,
                limit=limit,
                prefetch_limit=prefetch_limit,
                app_key=filters.get("app_key"),
                min_score=min_score,
                metadata_filters={k: v for k, v in filters.items() if k != "app_key"},
            )

            return [
                RetrievalResult(
                    doc_id=r.get("doc_id", f"qdrant_{idx}"),
                    text=r.get("content", ""),
                    score=r.get("score", 0.0),
                    source=self.backend_id,
                    rank=idx + 1,
                    metadata={
                        "dimension": dimension,
                        **r.get("metadata", {}),
                    },
                )
                for idx, r in enumerate(results)
            ]
        except Exception as e:
            logger.error(f"[QdrantHybridBackend] Retrieve failed: {e}")
            return []

    async def health_check(self) -> bool:
        """Qdrant 연결 상태 확인."""
        try:
            rag = self._get_rag("1D")
            stats = rag.get_collection_stats()
            return stats.get("available", False)
        except Exception:
            return False

    async def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """문서 인덱싱."""
        metadata = metadata or {}
        dimension = metadata.get("dimension", "1D")

        try:
            rag = self._get_rag(dimension)
            return rag.index_document(doc_id, text, metadata)
        except Exception as e:
            logger.error(f"[QdrantHybridBackend] Index failed: {e}")
            return False
```

### 4.4 NotebookLMBackend

```python
# backends/notebooklm.py
"""NotebookLM Backend.

NotebookLM Enterprise API를 통한 Grounded RAG.
tier0_notebooklm.py를 래핑.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseBackend, RetrievalResult

logger = logging.getLogger(__name__)


class NotebookLMBackend(BaseBackend):
    """NotebookLM Grounded RAG Backend.

    Features:
    - 거장 DNA 노트북 검색
    - 자동 인라인 인용
    - 환각률 13% (vs GPT-4o 40%)
    """

    backend_id = "notebooklm"

    def __init__(self):
        self._service = None

    def _get_service(self):
        """NotebookLM 서비스 (lazy load)."""
        if self._service is None:
            from app.rag.tier0_notebooklm import get_notebooklm_service
            self._service = get_notebooklm_service()
        return self._service

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """NotebookLM 검색.

        Config options:
            notebook_id: 노트북 ID (예: "DNA_봉준호")
            source_filter: 소스 필터 (예: "auteur_dna")
        """
        config = config or {}

        notebook_id = config.get("notebook_id")
        if not notebook_id:
            logger.warning("[NotebookLMBackend] notebook_id not specified")
            return []

        try:
            service = self._get_service()
            result = await service.query_notebook(
                notebook_id=notebook_id,
                query=query,
            )

            return [
                RetrievalResult(
                    doc_id=src.source_id,
                    text=src.text,
                    score=result.confidence,  # 전체 신뢰도 사용
                    source=self.backend_id,
                    rank=idx + 1,
                    metadata={
                        "notebook_id": notebook_id,
                        "grounded": result.grounded,
                    },
                )
                for idx, src in enumerate(result.sources[:limit])
            ]
        except Exception as e:
            logger.error(f"[NotebookLMBackend] Retrieve failed: {e}")
            return []

    async def health_check(self) -> bool:
        """NotebookLM 연결 상태 확인."""
        try:
            service = self._get_service()
            return service is not None
        except Exception:
            return False
```

### 4.5 VertexGroundingBackend

```python
# backends/vertex_grounding.py
"""Vertex AI RAG + Google Search Grounding Backend.

Vertex AI RAG Engine + Google Search Grounding.
tier0_vertex_rag.py를 래핑.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseBackend, RetrievalResult

logger = logging.getLogger(__name__)


class VertexGroundingBackend(BaseBackend):
    """Vertex AI RAG + Google Search Grounding Backend.

    Features:
    - Vertex AI RAG Engine (프라이빗 데이터)
    - Google Search Grounding (실시간 정보)
    """

    backend_id = "vertex_grounding"

    def __init__(self):
        self._service = None

    def _get_service(self):
        """Vertex RAG 서비스 (lazy load)."""
        if self._service is None:
            from app.rag.tier0_vertex_rag import get_vertex_rag_service
            self._service = get_vertex_rag_service()
        return self._service

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """Vertex AI RAG + Grounding 검색.

        Config options:
            corpus_name: Corpus 이름 (예: "auteur_dna")
            use_grounding: Google Search Grounding 사용 여부 (기본: True)
        """
        config = config or {}

        corpus_name = config.get("corpus_name")
        use_grounding = config.get("use_grounding", True)

        try:
            service = self._get_service()
            result = await service.query(
                query=query,
                corpus_name=corpus_name,
                use_grounding=use_grounding,
            )

            results = []

            # Vertex AI RAG 결과
            for idx, src in enumerate(result.sources[:limit]):
                results.append(RetrievalResult(
                    doc_id=src.source_id,
                    text=src.text,
                    score=result.confidence,
                    source=self.backend_id,
                    rank=idx + 1,
                    metadata={
                        "corpus_name": corpus_name,
                        "type": "vertex_rag",
                    },
                ))

            # Google Search Grounding 결과
            for idx, src in enumerate(result.grounding_sources):
                results.append(RetrievalResult(
                    doc_id=f"grounding_{idx}",
                    text=src.get("snippet", ""),
                    score=result.confidence * 0.9,  # Grounding은 약간 낮게
                    source=self.backend_id,
                    rank=len(result.sources) + idx + 1,
                    metadata={
                        "url": src.get("url"),
                        "type": "google_search",
                    },
                ))

            return results[:limit]
        except Exception as e:
            logger.error(f"[VertexGroundingBackend] Retrieve failed: {e}")
            return []

    async def health_check(self) -> bool:
        """Vertex AI 연결 상태 확인."""
        try:
            service = self._get_service()
            return service is not None
        except Exception:
            return False
```

---

## 5. YAML Manifest 확장

### 5.1 backends 필드 추가

P1에서 생성한 `_schema.yaml`에 `backends` 필드 추가:

```yaml
# manifests/_schema.yaml (추가)
properties:
  # ... 기존 필드 ...

  backends:
    type: array
    description: "사용할 백엔드 목록과 가중치"
    items:
      type: object
      properties:
        id:
          type: string
          enum: [qdrant_hybrid, notebooklm, vertex_grounding]
          description: "백엔드 ID (backends/ 디렉토리에서 자동 발견)"
        weight:
          type: number
          minimum: 0
          maximum: 1
          default: 1.0
          description: "RRF 융합 시 가중치"
        enabled:
          type: boolean
          default: true
        config:
          type: object
          additionalProperties: true
          description: "백엔드별 추가 설정"
      required: [id]
```

### 5.2 앱별 YAML 예시 (P3용 준비)

```yaml
# manifests/dimension.persona.yaml (확장)
app_key: dimension.persona.analyze
version: "1.1"

dimensions:
  - AI

# P2: 백엔드 설정 (P3 Ensemble용)
backends:
  - id: qdrant_hybrid
    weight: 0.6
    enabled: true
    config:
      dimension: AI
      prefetch_limit: 20

  - id: notebooklm
    weight: 0.3
    enabled: true
    config:
      notebook_id: DNA_봉준호
      source_filter: psychology

  - id: vertex_grounding
    weight: 0.1
    enabled: false  # 필요시 활성화
    config:
      use_grounding: true

# 기존 필드
dataset_routing:
  candidates: [psych_core, mbti, attachment, enneagram]
  # ...

search:
  limit: 5
  min_score: 0.5
```

---

## 6. manifest_loader.py 수정

### 6.1 BackendConfig 모델 추가

```python
# manifest_loader.py (추가)

class BackendConfig(BaseModel):
    """백엔드 설정."""

    id: str
    weight: float = Field(default=1.0, ge=0, le=1)
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class YAMLManifest(BaseModel):
    # ... 기존 필드 ...

    # P2: 백엔드 설정
    backends: List[BackendConfig] = Field(default_factory=list)
```

---

## 7. 구현 단계

### Step 1: backends/ 디렉토리 생성 (30분)
1. `backends/__init__.py` - Auto-discovery Registry
2. `backends/base.py` - BaseBackend ABC + RetrievalResult

### Step 2: 백엔드 구현체 마이그레이션 (1.5시간)
1. `backends/qdrant_hybrid.py` - tier1_dimension_rag 래핑
2. `backends/notebooklm.py` - tier0_notebooklm 래핑
3. `backends/vertex_grounding.py` - tier0_vertex_rag 래핑

### Step 3: manifest_loader.py 확장 (30분)
1. `BackendConfig` Pydantic 모델 추가
2. `YAMLManifest.backends` 필드 추가

### Step 4: 테스트 작성 (1시간)
1. `tests/test_backend_registry.py` - Registry 테스트
2. `tests/test_backends.py` - 각 백엔드 통합 테스트

### Step 5: 검증 및 문서화 (30분)
1. 전체 테스트 실행
2. CLAUDE.md 업데이트

---

## 8. 테스트 계획

### 8.1 단위 테스트

```python
# tests/test_backend_registry.py
class TestBackendRegistry:
    def test_auto_discovery(self):
        """백엔드 자동 발견."""
        from app.rag.backends import list_backends, reload_backends
        reload_backends()
        backends = list_backends()
        assert "qdrant_hybrid" in backends
        assert "notebooklm" in backends

    def test_get_backend(self):
        """백엔드 인스턴스 가져오기."""
        from app.rag.backends import get_backend
        backend = get_backend("qdrant_hybrid")
        assert backend is not None
        assert backend.backend_id == "qdrant_hybrid"

    def test_singleton(self):
        """백엔드 싱글톤 확인."""
        from app.rag.backends import get_backend
        b1 = get_backend("qdrant_hybrid")
        b2 = get_backend("qdrant_hybrid")
        assert b1 is b2
```

### 8.2 통합 테스트

```python
# tests/test_backends.py
@pytest.mark.asyncio
class TestQdrantHybridBackend:
    async def test_retrieve(self):
        """Qdrant Hybrid 검색."""
        from app.rag.backends import get_backend
        backend = get_backend("qdrant_hybrid")
        results = await backend.retrieve(
            query="봉준호 스타일",
            config={"dimension": "AD"},
        )
        assert isinstance(results, list)
        for r in results:
            assert hasattr(r, "doc_id")
            assert hasattr(r, "score")

    async def test_health_check(self):
        """Qdrant 헬스체크."""
        from app.rag.backends import get_backend
        backend = get_backend("qdrant_hybrid")
        healthy = await backend.health_check()
        assert isinstance(healthy, bool)
```

---

## 9. 검증 체크리스트

### 9.1 구현 완료 조건
- [ ] `backends/base.py` - BaseBackend ABC 정의
- [ ] `backends/__init__.py` - Auto-discovery Registry
- [ ] `backends/qdrant_hybrid.py` - Qdrant 백엔드
- [ ] `backends/notebooklm.py` - NotebookLM 백엔드
- [ ] `backends/vertex_grounding.py` - Vertex 백엔드
- [ ] `manifest_loader.py` - BackendConfig 추가
- [ ] `tests/test_backend_registry.py` - Registry 테스트
- [ ] `tests/test_backends.py` - 통합 테스트

### 9.2 테스트 명령어

```bash
# 테스트 실행
cd backend && source venv/bin/activate
pytest tests/test_backend_registry.py tests/test_backends.py -v

# 전체 RAG 테스트
pytest -v -k "backend or rag" tests/
```

### 9.3 수동 검증

```python
# Python REPL
from app.rag.backends import list_backends, get_backend, reload_backends

# 발견된 백엔드 확인
reload_backends()
print(list_backends())  # ['notebooklm', 'qdrant_hybrid', 'vertex_grounding']

# 백엔드 테스트
backend = get_backend("qdrant_hybrid")
print(backend)  # <QdrantHybridBackend(backend_id='qdrant_hybrid')>

# 검색 테스트 (async)
import asyncio
results = asyncio.run(backend.retrieve("봉준호", config={"dimension": "AD"}))
print(len(results), results[0] if results else None)
```

---

## 10. 다음 단계 (P3 미리보기)

P2 완료 후 P3에서:

| Phase | 작업 | 핵심 기능 |
|-------|------|----------|
| **P3** | Ensemble Retriever (병렬 RRF) | 다중 백엔드 병렬 실행 + Weighted RRF |

P3에서는 `hybrid_rag.py`에 `ensemble_retrieve()` 함수를 추가하여:
1. YAML manifest의 `backends` 설정 읽기
2. 활성화된 백엔드들 병렬 실행
3. Weighted RRF로 결과 융합

```python
# P3 미리보기: hybrid_rag.py
async def ensemble_retrieve(
    query: str,
    app_key: str,
    timeout: float = 5.0,
) -> List[RetrievalResult]:
    """병렬 Ensemble Retriever (P3)."""
    manifest = get_manifest(app_key)
    if not manifest or not manifest.backends:
        # Fallback to single backend
        return await get_backend("qdrant_hybrid").retrieve(query)

    # 병렬 실행 + Weighted RRF 융합
    # ...
```

---

## 11. 참고 자료

### 11.1 리서치 결과
- [Python Packaging - Creating and discovering plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
- [Python ABC Documentation](https://docs.python.org/3/library/abc.html)
- `pkgutil.iter_modules()` for internal plugin discovery
- `importlib.metadata.entry_points()` for external plugin discovery (Python 3.10+)

### 11.2 관련 문서
- 전체 계획: `/Users/ted/.gemini/antigravity/brain/.../implementation_plan.md.resolved`
- P1 완료: `ad6250e6` (YAML Manifest 도입)
- 프로젝트 가이드: `/Users/ted/vivid/CLAUDE.md`

---

## 12. 예상 소요 시간 요약

| 단계 | 작업 | 예상 시간 |
|------|------|----------|
| Step 1 | backends/ 디렉토리 + ABC | 30분 |
| Step 2 | 백엔드 구현체 3개 | 1.5시간 |
| Step 3 | manifest_loader 확장 | 30분 |
| Step 4 | 테스트 작성 | 1시간 |
| Step 5 | 검증 및 문서화 | 30분 |
| **합계** | | **4시간** |
