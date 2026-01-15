# P3: Ensemble Retriever SPEC

> **목표**: "오케스트레이터 수정 없이 백엔드 조합 변경"
>
> **상태**: Planning
>
> **선행 작업**: P0~P2 완료

---

## 1. 개요

### 1.1 배경

P2에서 Backend ABC와 Auto-discovery Registry를 구축했다. P3에서는 이를 기반으로 다중 백엔드를 병렬 실행하고 Weighted RRF로 결과를 융합하는 **Ensemble Retriever**를 구현한다.

### 1.2 핵심 원칙

```
"백엔드 조합 변경 = YAML 수정" (오케스트레이터 코드 수정 0)
```

### 1.3 선행 작업 요약

| Phase | 내용 | 상태 |
|-------|------|------|
| P0 | Qdrant Native Sparse Vector | ✅ 완료 |
| P0.5 | 전체 Dimension Hybrid 마이그레이션 | ✅ 완료 |
| P1 | YAML Manifest + Dataset Routing | ✅ 완료 |
| P2 | Backend ABC + Auto-discovery | ✅ 완료 |
| **P3** | **Ensemble Retriever (본 문서)** | 🔄 Planning |

---

## 2. 아키텍처

### 2.1 컴포넌트 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                        hybrid_rag.py                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   EnsembleRetriever                         ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │ manifest.backends[]                                     │││
│  │  │   - qdrant_hybrid (weight: 0.6)                        │││
│  │  │   - notebooklm (weight: 0.4)                           │││
│  │  └─────────────────────────────────────────────────────────┘││
│  │                         ↓                                   ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         ││
│  │  │ Qdrant      │  │ NotebookLM  │  │ Vertex      │  ...    ││
│  │  │ Hybrid      │  │ Backend     │  │ Grounding   │         ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘         ││
│  │         │                │                │                 ││
│  │         └────────────────┼────────────────┘                 ││
│  │                          ↓                                   ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │              Weighted RRF Fusion                        │││
│  │  │  score = Σ (weight_i / (k + rank_i))                   │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 데이터 플로우

```
1. Query 입력
2. YAMLManifest에서 backends[] 로드
3. 각 백엔드 병렬 실행 (asyncio.gather)
4. Weighted RRF로 결과 융합
5. 통합 RetrievalResult 반환
```

---

## 3. 구현 상세

### 3.1 새로운 파일 구조

```
backend/app/rag/backends/
├── __init__.py          # (P2) Auto-discovery Registry
├── base.py              # (P2) BaseBackend ABC, RetrievalResult
├── qdrant_hybrid.py     # (P2) Qdrant 백엔드
├── notebooklm.py        # (P2) NotebookLM 백엔드
├── vertex_grounding.py  # (P2) Vertex AI 백엔드
├── rrf.py               # (P3) Weighted RRF 알고리즘
└── ensemble.py          # (P3) EnsembleRetriever
```

### 3.2 backends/rrf.py

```python
"""Weighted Reciprocal Rank Fusion."""
from typing import Dict, List, Tuple
from .base import RetrievalResult


def weighted_rrf(
    result_lists: List[Tuple[List[RetrievalResult], float]],
    k: int = 60,
) -> List[RetrievalResult]:
    """Weighted RRF로 여러 백엔드 결과 융합.

    Args:
        result_lists: [(results, weight), ...] 튜플 리스트
        k: RRF 상수 (기본 60)

    Returns:
        융합된 RetrievalResult 리스트 (점수 내림차순)
    """
    doc_scores: Dict[str, Dict] = {}

    for results, weight in result_lists:
        for rank, result in enumerate(results, start=1):
            doc_id = result.doc_id
            rrf_contribution = weight / (k + rank)

            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "result": result,
                    "rrf_score": 0.0,
                    "sources": [],
                }

            doc_scores[doc_id]["rrf_score"] += rrf_contribution
            doc_scores[doc_id]["sources"].append(result.source)

    # 정렬 및 반환
    sorted_docs = sorted(
        doc_scores.values(),
        key=lambda x: x["rrf_score"],
        reverse=True,
    )

    return [
        RetrievalResult(
            doc_id=d["result"].doc_id,
            text=d["result"].text,
            score=d["rrf_score"],
            source="ensemble",
            rank=idx + 1,
            metadata={
                **d["result"].metadata,
                "original_sources": d["sources"],
            },
        )
        for idx, d in enumerate(sorted_docs)
    ]
```

### 3.3 backends/ensemble.py

```python
"""Ensemble Retriever - 다중 백엔드 병렬 실행 + Weighted RRF."""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base import BaseBackend, RetrievalResult
from . import get_backend
from .rrf import weighted_rrf

logger = logging.getLogger(__name__)


class EnsembleRetriever:
    """다중 백엔드 Ensemble 검색기.

    YAML manifest의 backends[] 설정을 기반으로
    병렬 검색 + Weighted RRF 융합.
    """

    def __init__(
        self,
        backends: List[tuple],  # [(backend, weight, config), ...]
        timeout: float = 10.0,
    ):
        self.backends = backends
        self.timeout = timeout

    @classmethod
    def from_manifest(cls, manifest: "YAMLManifest") -> "EnsembleRetriever":
        """YAML Manifest에서 EnsembleRetriever 생성."""
        backends = []
        for cfg in manifest.backends:
            if not cfg.enabled:
                continue
            backend = get_backend(cfg.id)
            if backend:
                backends.append((backend, cfg.weight, cfg.config))
            else:
                logger.warning(f"[Ensemble] Backend not found: {cfg.id}")
        return cls(backends=backends)

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """다중 백엔드 병렬 검색 + Weighted RRF.

        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            filters: 메타데이터 필터

        Returns:
            융합된 RetrievalResult 리스트
        """
        if not self.backends:
            logger.warning("[Ensemble] No backends configured")
            return []

        # 병렬 실행
        async def _fetch(backend, weight, config):
            try:
                results = await asyncio.wait_for(
                    backend.retrieve(query, limit * 2, filters, config),
                    timeout=self.timeout,
                )
                return (results, weight)
            except asyncio.TimeoutError:
                logger.warning(f"[Ensemble] Timeout: {backend.backend_id}")
                return ([], weight)
            except Exception as e:
                logger.error(f"[Ensemble] Error: {backend.backend_id}: {e}")
                return ([], weight)

        tasks = [
            _fetch(backend, weight, config)
            for backend, weight, config in self.backends
        ]

        result_lists = await asyncio.gather(*tasks)

        # 빈 결과 필터링
        valid_results = [(r, w) for r, w in result_lists if r]

        if not valid_results:
            logger.warning("[Ensemble] All backends returned empty")
            return []

        # Weighted RRF 융합
        fused = weighted_rrf(valid_results)

        logger.info(
            f"[Ensemble] Query '{query[:30]}...' | "
            f"backends={len(valid_results)}/{len(self.backends)} | "
            f"fused={len(fused)}"
        )

        return fused[:limit]


def get_ensemble_retriever(app_key: str) -> Optional[EnsembleRetriever]:
    """앱 키로 EnsembleRetriever 생성.

    Args:
        app_key: 앱 식별자

    Returns:
        EnsembleRetriever 또는 None
    """
    from app.rag.manifest_loader import get_manifest

    manifest = get_manifest(app_key)
    if not manifest or not manifest.backends:
        return None

    return EnsembleRetriever.from_manifest(manifest)
```

### 3.4 YAML Manifest 예시

```yaml
# backend/app/rag/manifests/dimension.aesthetic.direct.yaml
app_key: dimension.aesthetic.direct
version: "2.0"
description: "미학 디렉터 - Auteur DNA 분석"
dimensions: ["AD", "4D"]

# P3: 백엔드 설정
backends:
  - id: qdrant_hybrid
    weight: 0.6
    enabled: true
    config:
      dimension: AD
      prefetch_limit: 30
      min_score: 0.3
  - id: notebooklm
    weight: 0.4
    enabled: true
    config:
      notebook_id: DNA_봉준호

# P1: Dataset 라우팅
dataset_routing:
  candidates: [psych_core, film_analysis, visual_grammar]
  default: psych_core
  max_select: 2
```

---

## 4. hybrid_rag.py 통합

### 4.1 변경 전 (하드코딩)

```python
# 현재 코드 - 하드코딩된 백엔드 선택
async def _query_auteur_first(query, auteur_key, use_google_search):
    # NotebookLM 직접 호출
    notebooklm_result = await notebooklm_service.query_notebook(...)
    # Vertex AI 직접 호출
    vertex_result = await vertex_service.query(...)
```

### 4.2 변경 후 (Ensemble)

```python
# P3 리팩토링 - EnsembleRetriever 사용
from app.rag.backends.ensemble import get_ensemble_retriever

async def _query_with_ensemble(query, app_key, filters=None):
    retriever = get_ensemble_retriever(app_key)
    if retriever:
        return await retriever.retrieve(query, filters=filters)

    # Fallback: 기존 로직
    return await _query_auteur_first(...)
```

### 4.3 점진적 마이그레이션 전략

```
Phase 1: EnsembleRetriever 구현 (코드만 추가, 호출 안함)
Phase 2: hybrid_query()에서 선택적 사용 (feature flag)
Phase 3: manifest.backends 있는 앱만 Ensemble 사용
Phase 4: 전체 마이그레이션 후 레거시 코드 제거
```

---

## 5. 구현 단계

### Step 1: RRF 모듈 분리
- [ ] `backends/rrf.py` 생성
- [ ] `weighted_rrf()` 함수 구현
- [ ] 단위 테스트 작성

### Step 2: EnsembleRetriever 구현
- [ ] `backends/ensemble.py` 생성
- [ ] `EnsembleRetriever` 클래스 구현
- [ ] `get_ensemble_retriever()` 헬퍼 함수
- [ ] 통합 테스트 작성

### Step 3: YAML Manifest 작성
- [ ] `manifests/dimension.aesthetic.direct.yaml` 업데이트
- [ ] 다른 앱 매니페스트 업데이트

### Step 4: hybrid_rag.py 통합
- [ ] `_query_with_ensemble()` 함수 추가
- [ ] 기존 함수에서 선택적 호출
- [ ] 점진적 마이그레이션

### Step 5: 테스트 및 검증
- [ ] `tests/rag/test_rrf.py`
- [ ] `tests/rag/test_ensemble_retriever.py`
- [ ] 기존 테스트 회귀 확인

---

## 6. 테스트 계획

### 6.1 단위 테스트

```python
# tests/rag/test_rrf.py
class TestWeightedRRF:
    def test_single_backend(self):
        """단일 백엔드 결과 처리."""

    def test_weighted_fusion(self):
        """가중치 적용 융합 테스트."""

    def test_duplicate_doc_handling(self):
        """중복 문서 병합 테스트."""
```

### 6.2 통합 테스트

```python
# tests/rag/test_ensemble_retriever.py
class TestEnsembleRetriever:
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """병렬 실행 테스트."""

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """타임아웃 처리 테스트."""

    @pytest.mark.asyncio
    async def test_from_manifest(self):
        """YAML manifest 로딩 테스트."""
```

---

## 7. 성능 고려사항

### 7.1 병렬 실행

- `asyncio.gather()` 사용으로 latency 최소화
- 백엔드별 개별 타임아웃 (기본 10초)
- 실패한 백엔드는 결과에서 제외 (graceful degradation)

### 7.2 메모리

- 각 백엔드에서 `limit * 2` 결과 가져와서 RRF 후 `limit`개 반환
- 대규모 결과셋 처리 시 스트리밍 고려

### 7.3 캐싱

- 기존 `semantic_cache` 활용
- EnsembleRetriever 결과도 캐싱 가능

---

## 8. 검증 체크리스트

```bash
# P3 검증 명령어
cd backend && source venv/bin/activate

# 1. 단위 테스트
pytest tests/rag/test_rrf.py -v

# 2. 통합 테스트
pytest tests/rag/test_ensemble_retriever.py -v

# 3. 전체 RAG 테스트
pytest tests/rag/ --tb=short -q

# 4. 수동 검증
python -c "
from app.rag.backends.ensemble import get_ensemble_retriever
retriever = get_ensemble_retriever('dimension.aesthetic.direct')
print(f'Backends: {len(retriever.backends)}')
"
```

---

## 9. 롤백 계획

1. `backends/ensemble.py`, `backends/rrf.py` 제거
2. `hybrid_rag.py` 변경 사항 revert
3. YAML manifest의 `backends` 필드는 유지 (무시됨)

---

## 10. 관련 문서

| 문서 | 설명 |
|------|------|
| `P0_QDRANT_SPARSE_VECTOR_SPEC.md` | Qdrant Native Sparse |
| `P1_YAML_MANIFEST_SPEC.md` | YAML Manifest 도입 |
| `P2_BACKEND_ABC_SPEC.md` | Backend ABC + Registry |
| `DIMENSION_APP_DEVELOPER_GUIDE.md` | 앱 개발 가이드 |

---

**작성일**: 2026-01-15
**작성자**: Claude Opus 4.5
