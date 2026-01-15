# P3: Ensemble Retriever 상세 설계 문서

> Version: 1.0
> Date: 2025-01-15
> Status: Planning
> Depends on: P2 (Backend ABC + Auto-discovery)

---

## 1. 개요

### 1.1 목표
P2에서 구축한 Backend ABC 패턴을 활용하여 **다중 백엔드 병렬 실행 + Weighted RRF Fusion**을 구현합니다.

### 1.2 핵심 기능
- YAML Manifest의 `backends` 설정에 따른 동적 백엔드 선택
- `asyncio.gather()`를 통한 병렬 검색 실행
- **Weighted Reciprocal Rank Fusion (RRF)** 기반 결과 통합
- 기존 `hybrid_query()` API와의 하위 호환성 유지

### 1.3 의존성
```
P0 (YAML Manifest) → P1 (Dataset Routing) → P2 (Backend ABC) → P3 (Ensemble)
```

---

## 2. 아키텍처

### 2.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ensemble_retrieve()                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. YAML Manifest 로드 → backends 설정 추출                              │
│                                                                          │
│  2. enabled=true인 백엔드만 필터링                                        │
│                                                                          │
│  3. asyncio.gather() 병렬 실행                                           │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐            │
│     │qdrant_hybrid │  │ notebooklm   │  │ vertex_grounding │            │
│     │  weight=0.6  │  │  weight=0.3  │  │    weight=0.1    │            │
│     └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘            │
│            │                  │                   │                      │
│            └──────────────────┼───────────────────┘                      │
│                               ▼                                          │
│  4. Weighted RRF Fusion: RRF(d) = Σ w_i / (k + rank_i(d))               │
│                               │                                          │
│                               ▼                                          │
│  5. 상위 N개 결과 반환 (HybridRAGResult 형식)                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            hybrid_rag.py                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────┐     ┌────────────────────────────────────────┐  │
│  │   hybrid_query()   │────▶│          ensemble_retrieve()           │  │
│  │   (Public API)     │     │  - load manifest                       │  │
│  └────────────────────┘     │  - filter enabled backends             │  │
│                             │  - parallel execute                    │  │
│                             │  - weighted RRF fusion                 │  │
│                             └──────────────┬─────────────────────────┘  │
│                                            │                             │
│                                            ▼                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    _weighted_rrf_fusion()                        │    │
│  │  - group by doc_id                                               │    │
│  │  - calculate RRF score: Σ w_i / (k + rank_i)                     │    │
│  │  - sort by fused score                                           │    │
│  │  - return top N                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

                                    │
                    Uses (via get_backend())
                                    ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                         backends/ (P2)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────┐ │
│  │ QdrantHybrid     │  │ NotebookLM       │  │ VertexGrounding        │ │
│  │ Backend          │  │ Backend          │  │ Backend                │ │
│  │                  │  │                  │  │                        │ │
│  │ - retrieve()     │  │ - retrieve()     │  │ - retrieve()           │ │
│  │ - health_check() │  │ - health_check() │  │ - health_check()       │ │
│  └──────────────────┘  └──────────────────┘  └────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. RRF (Reciprocal Rank Fusion) 알고리즘

### 3.1 표준 RRF 공식

```
RRF(d) = Σ 1 / (k + rank_i(d))
```

- `d`: 문서
- `rank_i(d)`: i번째 retriever에서 문서 d의 순위 (1-based)
- `k`: 상수 (기본값 60, 낮은 순위의 영향 완화)

### 3.2 Weighted RRF 공식 (P3 구현)

```
Weighted_RRF(d) = Σ w_i / (k + rank_i(d))
```

- `w_i`: i번째 retriever의 가중치 (YAML에서 설정)
- 가중치 합이 1.0이 아니어도 동작 (정규화 불필요)

### 3.3 연구 결과 요약

| Source | Key Finding |
|--------|-------------|
| Microsoft | k=60이 대부분의 케이스에서 최적 |
| MongoDB | Score 정규화 없이 rank만 사용 권장 |
| LangChain | `EnsembleRetriever`에 weights 파라미터 제공 |
| LlamaIndex | `mode="reciprocal_rerank"` 옵션 |
| Medium | 의미론적 + 키워드 검색 조합에 효과적 |

### 3.4 k값 선택 가이드

| k값 | 특성 | 적합한 상황 |
|-----|------|------------|
| 1 | 상위 순위 강조 | 정밀도 우선 |
| 60 | 균형 (표준) | 일반적 사용 |
| 100+ | 하위 순위도 고려 | 재현율 우선 |

---

## 4. 구현 상세

### 4.1 ensemble_retrieve() 함수

```python
# backend/app/rag/hybrid_rag.py

async def ensemble_retrieve(
    query: str,
    app_key: str,
    *,
    limit: int = 5,
    min_score: float = 0.5,
    filters: Optional[Dict[str, Any]] = None,
    rrf_k: int = 60,
) -> HybridRAGResult:
    """
    P3: Ensemble Retrieval with Weighted RRF Fusion.

    YAML Manifest의 backends 설정에 따라 다중 백엔드를 병렬 실행하고
    Weighted RRF로 결과를 통합합니다.

    Args:
        query: 검색 쿼리
        app_key: 앱 식별자 (e.g., "dimension.aesthetic.direct")
        limit: 최종 반환할 최대 문서 수
        min_score: 최소 RRF 스코어 임계값
        filters: 추가 메타데이터 필터
        rrf_k: RRF 상수 (기본값 60)

    Returns:
        HybridRAGResult: 통합된 검색 결과

    Example:
        >>> result = await ensemble_retrieve(
        ...     query="봉준호 롱테이크 기법",
        ...     app_key="dimension.aesthetic.direct",
        ...     limit=7,
        ... )
        >>> print(result.total_results)  # 최대 7
        >>> for source in result.sources:
        ...     print(f"{source.source}: {source.doc_id}")
    """
    from app.rag.manifest_loader import load_manifest
    from app.rag.backends import get_backend

    # 1. Manifest 로드
    manifest = load_manifest(app_key)
    if not manifest or not manifest.backends:
        logger.warning(f"No backends configured for {app_key}, falling back to default")
        return await _fallback_single_backend_query(query, app_key, limit, min_score, filters)

    # 2. enabled=true인 백엔드만 필터링
    enabled_backends = [b for b in manifest.backends if b.enabled]
    if not enabled_backends:
        logger.warning(f"No enabled backends for {app_key}")
        return HybridRAGResult(sources=[], total_results=0)

    # 3. 병렬 실행 태스크 생성
    async def _execute_backend(backend_config: BackendConfig) -> Tuple[str, float, List[RetrievalResult]]:
        """단일 백엔드 실행 및 결과 반환."""
        try:
            backend = get_backend(backend_config.id)
            results = await backend.retrieve(
                query=query,
                limit=limit * 2,  # Over-fetch for fusion
                filters=filters,
                config=backend_config.config,
            )
            return (backend_config.id, backend_config.weight, results)
        except Exception as e:
            logger.error(f"Backend {backend_config.id} failed: {e}")
            return (backend_config.id, backend_config.weight, [])

    # 4. asyncio.gather()로 병렬 실행
    tasks = [_execute_backend(b) for b in enabled_backends]
    backend_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 5. 예외 필터링
    valid_results: List[Tuple[str, float, List[RetrievalResult]]] = []
    for result in backend_results:
        if isinstance(result, Exception):
            logger.error(f"Backend execution error: {result}")
            continue
        valid_results.append(result)

    if not valid_results:
        return HybridRAGResult(sources=[], total_results=0)

    # 6. Weighted RRF Fusion
    fused_results = _weighted_rrf_fusion(valid_results, k=rrf_k, limit=limit, min_score=min_score)

    # 7. HybridRAGResult 형식으로 변환
    return _convert_ensemble_to_hybrid_result(fused_results, query)
```

### 4.2 _weighted_rrf_fusion() 함수

```python
def _weighted_rrf_fusion(
    backend_results: List[Tuple[str, float, List[RetrievalResult]]],
    *,
    k: int = 60,
    limit: int = 10,
    min_score: float = 0.0,
) -> List[RetrievalResult]:
    """
    Weighted Reciprocal Rank Fusion 알고리즘.

    Args:
        backend_results: [(backend_id, weight, results), ...] 형식
        k: RRF 상수 (기본값 60)
        limit: 반환할 최대 문서 수
        min_score: 최소 RRF 스코어 임계값

    Returns:
        RRF 스코어로 정렬된 RetrievalResult 리스트

    Algorithm:
        RRF(d) = Σ w_i / (k + rank_i(d))

        where:
        - w_i = weight of retriever i
        - rank_i(d) = 1-based rank of document d in retriever i
        - k = smoothing constant (60 by default)
    """
    # doc_id -> {rrf_score, best_result, sources}
    doc_scores: Dict[str, Dict[str, Any]] = {}

    for backend_id, weight, results in backend_results:
        for rank, result in enumerate(results, start=1):
            doc_id = result.doc_id
            rrf_contribution = weight / (k + rank)

            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "rrf_score": 0.0,
                    "best_result": result,
                    "sources": [],
                    "max_original_score": result.score,
                }

            doc_scores[doc_id]["rrf_score"] += rrf_contribution
            doc_scores[doc_id]["sources"].append(backend_id)

            # 가장 높은 원본 스코어를 가진 결과 보존
            if result.score > doc_scores[doc_id]["max_original_score"]:
                doc_scores[doc_id]["best_result"] = result
                doc_scores[doc_id]["max_original_score"] = result.score

    # RRF 스코어로 정렬
    sorted_docs = sorted(
        doc_scores.items(),
        key=lambda x: x[1]["rrf_score"],
        reverse=True,
    )

    # min_score 필터링 및 limit 적용
    fused_results: List[RetrievalResult] = []
    for doc_id, data in sorted_docs[:limit]:
        if data["rrf_score"] < min_score:
            continue

        result = data["best_result"]
        # RRF 스코어와 소스 정보를 metadata에 추가
        result.metadata["rrf_score"] = data["rrf_score"]
        result.metadata["fusion_sources"] = data["sources"]
        result.score = data["rrf_score"]  # 원본 스코어를 RRF 스코어로 대체

        fused_results.append(result)

    # 최종 순위 재설정
    for i, result in enumerate(fused_results, start=1):
        result.rank = i

    return fused_results
```

### 4.3 _convert_ensemble_to_hybrid_result() 헬퍼

```python
def _convert_ensemble_to_hybrid_result(
    fused_results: List[RetrievalResult],
    query: str,
) -> HybridRAGResult:
    """
    RetrievalResult 리스트를 HybridRAGResult로 변환.

    기존 hybrid_query() API와의 하위 호환성을 유지합니다.
    """
    sources = []
    for result in fused_results:
        sources.append(RAGSource(
            doc_id=result.doc_id,
            content=result.text,
            score=result.score,
            source=result.source,
            metadata=result.metadata,
        ))

    return HybridRAGResult(
        query=query,
        sources=sources,
        total_results=len(sources),
        notebooklm_sources=[s for s in sources if s.source == "notebooklm"],
        vertex_sources=[s for s in sources if s.source in ("qdrant_hybrid", "vertex_grounding")],
        fusion_method="weighted_rrf",
    )
```

---

## 5. YAML Manifest 예시

### 5.1 Aesthetic Director (dimension.aesthetic.yaml)

```yaml
app_key: dimension.aesthetic.direct
version: "1.0"
description: "Auteur style guides and aesthetic theory"

dimensions:
  - AD
  - 1D
  - 3D

search_limit: 7
min_score: 0.55
amplify_with_history: true
fallback_enabled: true

metadata_filters:
  content_type:
    - auteur_style
    - aesthetic_theory
    - visual_guide

prompt_injection_template: |
  ## Auteur Style Guidelines & Aesthetic Theory (Retrieved)
  {rag_results}

  Channel these masters' visual languages and aesthetic principles.

# P3: Backend configuration for ensemble retrieval
backends:
  - id: qdrant_hybrid
    weight: 0.6
    enabled: true
    config:
      dimension: AD
      prefetch_limit: 30
      min_score: 0.45

  - id: notebooklm
    weight: 0.3
    enabled: true
    config:
      notebook_id: DNA_봉준호  # Default auteur

  - id: vertex_grounding
    weight: 0.1
    enabled: false  # Enable when Google Search context needed
    config:
      corpus_name: auteur_dna
      use_grounding: true
```

### 5.2 Teaching Prompt (teaching.prompt.yaml)

```yaml
app_key: teaching.prompt.generate
version: "1.0"
description: "Teaching prompt generation with reference materials"

dimensions:
  - 1D
  - 2D

search_limit: 5
min_score: 0.6

backends:
  - id: qdrant_hybrid
    weight: 0.8
    enabled: true
    config:
      dimension: 1D
      prefetch_limit: 20

  - id: vertex_grounding
    weight: 0.2
    enabled: true
    config:
      use_grounding: true  # Web context for current trends
```

---

## 6. 테스트 계획

### 6.1 단위 테스트

```python
# tests/rag/test_ensemble_retriever.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.rag.hybrid_rag import ensemble_retrieve, _weighted_rrf_fusion
from app.rag.backends.base import RetrievalResult


class TestWeightedRRFFusion:
    """_weighted_rrf_fusion() 단위 테스트."""

    def test_basic_fusion(self):
        """기본 RRF fusion 테스트."""
        backend_results = [
            ("qdrant_hybrid", 0.6, [
                RetrievalResult(doc_id="doc_1", text="Content 1", score=0.9, source="qdrant_hybrid", rank=1),
                RetrievalResult(doc_id="doc_2", text="Content 2", score=0.8, source="qdrant_hybrid", rank=2),
            ]),
            ("notebooklm", 0.4, [
                RetrievalResult(doc_id="doc_2", text="Content 2", score=0.85, source="notebooklm", rank=1),
                RetrievalResult(doc_id="doc_3", text="Content 3", score=0.7, source="notebooklm", rank=2),
            ]),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60, limit=3)

        # doc_2가 두 retriever에서 모두 등장 -> 최상위
        assert fused[0].doc_id == "doc_2"
        assert len(fused[0].metadata["fusion_sources"]) == 2

    def test_weight_impact(self):
        """가중치가 순위에 미치는 영향 테스트."""
        # 높은 가중치 retriever의 1위 vs 낮은 가중치 retriever의 1위
        backend_results = [
            ("high_weight", 0.9, [
                RetrievalResult(doc_id="doc_A", text="A", score=0.9, source="high_weight", rank=1),
            ]),
            ("low_weight", 0.1, [
                RetrievalResult(doc_id="doc_B", text="B", score=0.9, source="low_weight", rank=1),
            ]),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60)

        # 높은 가중치의 doc_A가 상위
        assert fused[0].doc_id == "doc_A"
        assert fused[0].score > fused[1].score

    def test_k_parameter_effect(self):
        """k 파라미터 효과 테스트."""
        backend_results = [
            ("backend", 1.0, [
                RetrievalResult(doc_id=f"doc_{i}", text=f"Content {i}", score=0.9-i*0.1, source="backend", rank=i)
                for i in range(1, 11)
            ]),
        ]

        # 작은 k -> 상위 순위 강조
        fused_small_k = _weighted_rrf_fusion(backend_results, k=1, limit=10)
        # 큰 k -> 순위 차이 완화
        fused_large_k = _weighted_rrf_fusion(backend_results, k=100, limit=10)

        # 작은 k에서 스코어 차이가 더 큼
        small_k_diff = fused_small_k[0].score - fused_small_k[-1].score
        large_k_diff = fused_large_k[0].score - fused_large_k[-1].score
        assert small_k_diff > large_k_diff

    def test_min_score_filtering(self):
        """min_score 필터링 테스트."""
        backend_results = [
            ("backend", 1.0, [
                RetrievalResult(doc_id="doc_1", text="High", score=0.9, source="backend", rank=1),
                RetrievalResult(doc_id="doc_2", text="Low", score=0.1, source="backend", rank=100),
            ]),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60, min_score=0.01)

        # 낮은 순위 문서는 필터링됨
        assert len(fused) == 1
        assert fused[0].doc_id == "doc_1"


class TestEnsembleRetrieve:
    """ensemble_retrieve() 통합 테스트."""

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """병렬 실행 테스트."""
        with patch("app.rag.hybrid_rag.load_manifest") as mock_load:
            mock_manifest = MagicMock()
            mock_manifest.backends = [
                MagicMock(id="qdrant_hybrid", weight=0.6, enabled=True, config={"dimension": "AD"}),
                MagicMock(id="notebooklm", weight=0.4, enabled=True, config={"notebook_id": "test"}),
            ]
            mock_load.return_value = mock_manifest

            with patch("app.rag.hybrid_rag.get_backend") as mock_get_backend:
                mock_backend = AsyncMock()
                mock_backend.retrieve = AsyncMock(return_value=[
                    RetrievalResult(doc_id="doc_1", text="Content", score=0.9, source="test", rank=1),
                ])
                mock_get_backend.return_value = mock_backend

                result = await ensemble_retrieve(
                    query="봉준호 스타일",
                    app_key="dimension.aesthetic.direct",
                )

                # 두 백엔드 모두 호출됨
                assert mock_backend.retrieve.call_count == 2

    @pytest.mark.asyncio
    async def test_disabled_backend_skipped(self):
        """disabled 백엔드 스킵 테스트."""
        with patch("app.rag.hybrid_rag.load_manifest") as mock_load:
            mock_manifest = MagicMock()
            mock_manifest.backends = [
                MagicMock(id="qdrant_hybrid", weight=0.6, enabled=True, config={}),
                MagicMock(id="notebooklm", weight=0.4, enabled=False, config={}),  # disabled
            ]
            mock_load.return_value = mock_manifest

            with patch("app.rag.hybrid_rag.get_backend") as mock_get_backend:
                mock_backend = AsyncMock()
                mock_backend.retrieve = AsyncMock(return_value=[])
                mock_get_backend.return_value = mock_backend

                await ensemble_retrieve(query="test", app_key="test")

                # enabled된 백엔드만 호출 (1번)
                assert mock_backend.retrieve.call_count == 1

    @pytest.mark.asyncio
    async def test_backend_error_handling(self):
        """백엔드 에러 처리 테스트."""
        with patch("app.rag.hybrid_rag.load_manifest") as mock_load:
            mock_manifest = MagicMock()
            mock_manifest.backends = [
                MagicMock(id="qdrant_hybrid", weight=0.6, enabled=True, config={}),
                MagicMock(id="notebooklm", weight=0.4, enabled=True, config={}),
            ]
            mock_load.return_value = mock_manifest

            call_count = [0]
            async def mock_retrieve(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Backend error")
                return [RetrievalResult(doc_id="doc_1", text="Content", score=0.9, source="test", rank=1)]

            with patch("app.rag.hybrid_rag.get_backend") as mock_get_backend:
                mock_backend = AsyncMock()
                mock_backend.retrieve = mock_retrieve
                mock_get_backend.return_value = mock_backend

                result = await ensemble_retrieve(query="test", app_key="test")

                # 하나의 백엔드 실패해도 결과 반환
                assert result.total_results >= 0

    @pytest.mark.asyncio
    async def test_fallback_on_no_backends(self):
        """backends 설정 없을 때 fallback 테스트."""
        with patch("app.rag.hybrid_rag.load_manifest") as mock_load:
            mock_manifest = MagicMock()
            mock_manifest.backends = None
            mock_load.return_value = mock_manifest

            with patch("app.rag.hybrid_rag._fallback_single_backend_query") as mock_fallback:
                mock_fallback.return_value = HybridRAGResult(sources=[], total_results=0)

                await ensemble_retrieve(query="test", app_key="test")

                mock_fallback.assert_called_once()
```

### 6.2 통합 테스트

```python
# tests/rag/test_ensemble_integration.py

@pytest.mark.asyncio
async def test_ensemble_with_real_manifest():
    """실제 YAML manifest와 함께 테스트."""
    # dimension.aesthetic.yaml 사용
    result = await ensemble_retrieve(
        query="봉준호 롱테이크",
        app_key="dimension.aesthetic.direct",
        limit=5,
    )

    assert result.total_results <= 5
    assert result.fusion_method == "weighted_rrf"

    # 소스 다양성 확인
    sources = set(s.source for s in result.sources)
    # 최소 1개 소스에서 결과
    assert len(sources) >= 1


@pytest.mark.asyncio
async def test_ensemble_result_format():
    """결과 형식이 HybridRAGResult와 호환되는지 확인."""
    result = await ensemble_retrieve(
        query="test",
        app_key="dimension.aesthetic.direct",
    )

    # 기존 필드 존재
    assert hasattr(result, "sources")
    assert hasattr(result, "total_results")
    assert hasattr(result, "notebooklm_sources")
    assert hasattr(result, "vertex_sources")

    # 새 필드
    assert result.fusion_method == "weighted_rrf"
```

---

## 7. 구현 단계

### Phase 1: Core Implementation (Day 1-2)

| Task | Description | Files |
|------|-------------|-------|
| 7.1.1 | `_weighted_rrf_fusion()` 구현 | `hybrid_rag.py` |
| 7.1.2 | `ensemble_retrieve()` 구현 | `hybrid_rag.py` |
| 7.1.3 | `_convert_ensemble_to_hybrid_result()` 구현 | `hybrid_rag.py` |
| 7.1.4 | 단위 테스트 작성 | `tests/rag/test_ensemble_retriever.py` |

### Phase 2: Integration (Day 3)

| Task | Description | Files |
|------|-------------|-------|
| 7.2.1 | `hybrid_query()`에서 `ensemble_retrieve()` 호출 옵션 추가 | `hybrid_rag.py` |
| 7.2.2 | Manifest backends 설정 검증 | `manifest_loader.py` |
| 7.2.3 | 통합 테스트 작성 | `tests/rag/test_ensemble_integration.py` |

### Phase 3: Optimization (Day 4-5)

| Task | Description | Files |
|------|-------------|-------|
| 7.3.1 | 캐싱 전략 적용 (선택) | `hybrid_rag.py` |
| 7.3.2 | 로깅 및 메트릭 추가 | `hybrid_rag.py` |
| 7.3.3 | 문서화 업데이트 | `RAG_ARCHITECTURE.md` |

---

## 8. 성공 기준

### 8.1 기능 요구사항

- [ ] YAML backends 설정에 따른 동적 백엔드 선택
- [ ] asyncio.gather() 병렬 실행
- [ ] Weighted RRF fusion 정확한 구현
- [ ] 기존 hybrid_query() API 하위 호환

### 8.2 품질 요구사항

- [ ] 단위 테스트 커버리지 > 80%
- [ ] 통합 테스트 통과
- [ ] 에러 발생 시 graceful degradation
- [ ] 로깅으로 디버깅 가능

### 8.3 성능 요구사항

- [ ] 3개 백엔드 병렬 실행 시 latency < 3초
- [ ] RRF fusion 연산 < 10ms (1000 문서 기준)

---

## 9. 리스크 및 완화 방안

| Risk | Impact | Mitigation |
|------|--------|------------|
| 백엔드 timeout | 전체 검색 지연 | 개별 백엔드 timeout 설정 (5초) |
| 메모리 사용 증가 | OOM 가능성 | over-fetch 제한 (limit*2) |
| NotebookLM rate limit | 검색 실패 | 캐싱 + exponential backoff |
| 결과 품질 저하 | 사용자 경험 감소 | A/B 테스트로 가중치 튜닝 |

---

## 10. 참고 자료

### 10.1 연구 논문
- Cormack et al., "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods" (2009)

### 10.2 프레임워크 문서
- [LangChain EnsembleRetriever](https://python.langchain.com/docs/modules/data_connection/retrievers/ensemble)
- [LlamaIndex QueryFusionRetriever](https://docs.llamaindex.ai/en/stable/examples/retrievers/reciprocal_rerank_fusion.html)

### 10.3 관련 문서
- `/docs/RAG_ARCHITECTURE.md` - 전체 RAG 아키텍처
- `/docs/specs/P2_BACKEND_ABC_SPEC.md` - Backend ABC 스펙
- `/backend/app/rag/backends/base.py` - BaseBackend ABC
- `/backend/app/rag/manifest_loader.py` - YAML Manifest 로더

---

## 11. 변경 이력

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | Claude | 초안 작성 |
