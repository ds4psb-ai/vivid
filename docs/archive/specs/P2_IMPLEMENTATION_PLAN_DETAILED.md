# P2: Backend ABC + Auto-discovery 상세 구현 플랜

> **작성일**: 2026-01-15 | **상태**: ✅ 핵심 구현 완료, 마무리 작업 필요
> **커밋**: `fa5f4499` feat(rag): P2 - Backend ABC + Auto-discovery 구현

---

## 1. P2 구현 상태 요약

### 1.1 완료된 작업 ✅

| 파일 | LOC | 상태 | 설명 |
|------|-----|------|------|
| `backends/base.py` | 108 | ✅ | BaseBackend ABC + RetrievalResult dataclass |
| `backends/__init__.py` | 148 | ✅ | Auto-discovery Registry (pkgutil 기반) |
| `backends/qdrant_hybrid.py` | 119 | ✅ | Qdrant Dense+Sparse Hybrid 래핑 |
| `backends/notebooklm.py` | 95 | ✅ | NotebookLM Grounded RAG 래핑 |
| `backends/vertex_grounding.py` | 118 | ✅ | Vertex AI + Google Search 래핑 |
| `manifest_loader.py` | +19 | ✅ | BackendConfig Pydantic 모델 |
| `tests/rag/test_backend_registry.py` | 135 | ✅ | Registry 단위 테스트 (10개) |
| `tests/rag/test_backends.py` | 314 | ✅ | 백엔드 통합 테스트 (14개) |

### 1.2 테스트 결과

```
24 passed in 0.97s ✅
- TestBackendRegistry: 6 tests
- TestRetrievalResult: 2 tests
- TestBaseBackend: 2 tests
- TestQdrantHybridBackend: 5 tests
- TestNotebookLMBackend: 3 tests
- TestVertexGroundingBackend: 3 tests
- TestBackendConfig: 3 tests
```

### 1.3 미완료 작업 ⚠️

| 작업 | 우선순위 | 설명 |
|------|----------|------|
| `_schema.yaml` backends 필드 | P2 | YAML 스키마에 backends 정의 추가 |
| 앱별 YAML backends 설정 | P3 준비 | dimension.aesthetic.yaml 등에 예시 추가 |
| hybrid_rag.py 통합 | P3 범위 | Backend Registry를 통한 호출 |

---

## 2. 현재 아키텍처 분석

### 2.1 구현된 패턴

```
┌─────────────────────────────────────────────────────────────┐
│                    P2 구현 완료 아키텍처                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                        │
│  │ manifest_loader │──┬── BackendConfig (Pydantic)          │
│  │   (YAML 설정)   │  │   - id: str                         │
│  └─────────────────┘  │   - weight: float (0-1)             │
│                       │   - enabled: bool                    │
│                       │   - config: Dict                     │
│                       └────────────────────────────────────┐ │
│                                                            │ │
│  ┌────────────────────────────────────────────────────────┐│ │
│  │            Backend Registry (Auto-discovery)           ││ │
│  │  backends/__init__.py                                  ││ │
│  ├────────────────────────────────────────────────────────┤│ │
│  │  • _discover_backends() - pkgutil.iter_modules        ││ │
│  │  • get_backend(id) → BaseBackend (singleton)          ││ │
│  │  • list_backends() → ["qdrant_hybrid", ...]           ││ │
│  │  • reload_backends() → int (hot reload)               ││ │
│  └────────────────────────────────────────────────────────┘│ │
│                              │                              │ │
│     ┌────────────────────────┼────────────────────────┐     │ │
│     ▼                        ▼                        ▼     │ │
│  ┌────────────┐    ┌──────────────┐    ┌─────────────┐     │ │
│  │QdrantHybrid│    │NotebookLM    │    │Vertex       │     │ │
│  │Backend     │    │Backend       │    │Grounding    │     │ │
│  │            │    │              │    │Backend      │     │ │
│  │backend_id= │    │backend_id=   │    │backend_id=  │     │ │
│  │"qdrant_    │    │"notebooklm"  │    │"vertex_     │     │ │
│  │ hybrid"    │    │              │    │ grounding"  │     │ │
│  └──────┬─────┘    └──────┬───────┘    └──────┬──────┘     │ │
│         │                 │                   │             │ │
│         └─────────────────┼───────────────────┘             │ │
│                           ▼                                 │ │
│  ┌────────────────────────────────────────────────────────┐│ │
│  │              BaseBackend (ABC)                         ││ │
│  │  backends/base.py                                      ││ │
│  ├────────────────────────────────────────────────────────┤│ │
│  │  @abstractmethod                                       ││ │
│  │  async def retrieve(query, limit, filters, config)     ││ │
│  │      → List[RetrievalResult]                           ││ │
│  │                                                        ││ │
│  │  @abstractmethod                                       ││ │
│  │  async def health_check() → bool                       ││ │
│  │                                                        ││ │
│  │  async def index_document(doc_id, text, metadata)      ││ │
│  │      → bool (optional, default False)                  ││ │
│  └────────────────────────────────────────────────────────┘│ │
│                                                             │ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              RetrievalResult (dataclass)               │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  doc_id: str                                           │ │
│  │  text: str                                             │ │
│  │  score: float (0.0 ~ 1.0)                              │ │
│  │  source: str (backend_id)                              │ │
│  │  rank: int (1부터 시작)                                 │ │
│  │  metadata: Dict[str, Any]                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Plugin Discovery 패턴 (Python Best Practice)

현재 구현은 **Python Packaging User Guide**의 권장 패턴을 따름:

```python
# backends/__init__.py - pkgutil.iter_modules 기반
for finder, name, ispkg in pkgutil.iter_modules([str(backend_dir)]):
    if name.startswith("_") or name == "base":
        continue
    module = importlib.import_module(f".{name}", __package__)
    # BaseBackend 서브클래스 탐색...
```

**장점:**
- 외부 패키지 의존성 없음 (stdlib only)
- Hot reload 지원 (`reload_backends()`)
- 싱글톤 패턴으로 리소스 효율적

**대안 (미래 확장용):**
```python
# entry_points 기반 (외부 플러그인 지원 시)
from importlib.metadata import entry_points
discovered_plugins = entry_points(group='vivid.rag.backends')
```

---

## 3. 남은 작업 상세

### 3.1 _schema.yaml backends 필드 추가 (P2 범위)

**현재 상태:** 누락됨

**추가할 내용:**
```yaml
# manifests/_schema.yaml (추가할 섹션)

  # P2: Backend configuration
  backends:
    type: array
    description: "사용할 백엔드 목록과 가중치 (P3 Ensemble용)"
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
          description: "백엔드 활성화 여부"
        config:
          type: object
          additionalProperties: true
          description: "백엔드별 추가 설정"
      required: [id]
```

### 3.2 앱별 YAML backends 설정 예시 (P3 준비)

**dimension.aesthetic.yaml 확장:**
```yaml
app_key: dimension.aesthetic.direct
version: "1.1"

dimensions:
  - AD
  - 1D
  - 3D

# P3 준비: 백엔드 설정
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
      notebook_id: DNA_봉준호
      source_filter: auteur_style

  - id: vertex_grounding
    weight: 0.1
    enabled: false  # 필요시 활성화
    config:
      corpus_name: auteur_dna
      use_grounding: true

# 기존 필드 유지...
search_limit: 7
min_score: 0.55
```

---

## 4. P3 Ensemble Retriever 설계

### 4.1 목표 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    P3 목표 아키텍처                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  hybrid_query()                                             │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           ensemble_retrieve() [NEW]                  │   │
│  │  1. get_manifest(app_key) → backends 설정            │   │
│  │  2. 활성화된 백엔드들 병렬 실행                        │   │
│  │  3. Weighted RRF로 결과 융합                          │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │                                  │
│          ┌───────────────┼───────────────┐                  │
│          ▼               ▼               ▼                  │
│     ┌─────────┐    ┌──────────┐    ┌──────────┐            │
│     │ Backend │    │ Backend  │    │ Backend  │            │
│     │Registry │───▶│ Registry │───▶│ Registry │            │
│     │.get()   │    │.get()    │    │.get()    │            │
│     └────┬────┘    └────┬─────┘    └────┬─────┘            │
│          │              │               │                   │
│          ▼              ▼               ▼                   │
│   QdrantHybrid    NotebookLM      Vertex                   │
│   Backend         Backend         Grounding                 │
│                                                             │
│          │              │               │                   │
│          └──────────────┴───────────────┘                   │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Weighted RRF Fusion                     │   │
│  │  score = Σ (weight_i / (k + rank_i))                │   │
│  │  k = 60 (상수), weight = backend.weight             │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│              List[RetrievalResult] (통합 결과)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 ensemble_retrieve() 구현 계획

```python
# hybrid_rag.py에 추가할 함수

async def ensemble_retrieve(
    query: str,
    app_key: str,
    filters: Optional[Dict[str, Any]] = None,
    timeout: float = 5.0,
) -> List[RetrievalResult]:
    """P3: 병렬 Ensemble Retriever.

    YAML manifest의 backends 설정에 따라 다중 백엔드 병렬 실행 후
    Weighted RRF로 결과 융합.

    Args:
        query: 검색 쿼리
        app_key: 앱 식별자 (manifest lookup)
        filters: 공통 필터 (app_key, dataset_id 등)
        timeout: 백엔드 타임아웃 (초)

    Returns:
        융합된 RetrievalResult 리스트 (score 내림차순)
    """
    from app.rag.backends import get_backend
    from app.rag.manifest_loader import get_manifest

    manifest = get_manifest(app_key)
    if not manifest or not manifest.backends:
        # Fallback: qdrant_hybrid만 사용
        backend = get_backend("qdrant_hybrid")
        return await backend.retrieve(query, filters=filters)

    # 활성화된 백엔드만 필터
    enabled_backends = [b for b in manifest.backends if b.enabled]

    # 병렬 실행
    async def _fetch(backend_config):
        backend = get_backend(backend_config.id)
        if not backend:
            return []
        try:
            return await asyncio.wait_for(
                backend.retrieve(
                    query=query,
                    filters=filters,
                    config=backend_config.config,
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"[Ensemble] Timeout: {backend_config.id}")
            return []
        except Exception as e:
            logger.error(f"[Ensemble] Error in {backend_config.id}: {e}")
            return []

    results_lists = await asyncio.gather(
        *[_fetch(bc) for bc in enabled_backends]
    )

    # Weighted RRF Fusion
    return _weighted_rrf_fusion(
        results_lists=results_lists,
        weights=[bc.weight for bc in enabled_backends],
        k=60,
    )


def _weighted_rrf_fusion(
    results_lists: List[List[RetrievalResult]],
    weights: List[float],
    k: int = 60,
) -> List[RetrievalResult]:
    """Weighted Reciprocal Rank Fusion.

    score(d) = Σ (weight_i / (k + rank_i(d)))
    """
    doc_scores: Dict[str, float] = {}
    doc_results: Dict[str, RetrievalResult] = {}

    for results, weight in zip(results_lists, weights):
        for result in results:
            key = result.doc_id
            rrf_score = weight / (k + result.rank)
            doc_scores[key] = doc_scores.get(key, 0.0) + rrf_score

            # 첫 등장 결과 저장 (또는 더 높은 원본 score)
            if key not in doc_results or result.score > doc_results[key].score:
                doc_results[key] = result

    # score 업데이트 및 정렬
    fused = []
    for doc_id, rrf_score in sorted(doc_scores.items(), key=lambda x: -x[1]):
        result = doc_results[doc_id]
        fused.append(RetrievalResult(
            doc_id=result.doc_id,
            text=result.text,
            score=rrf_score,  # RRF score로 대체
            source=result.source,
            rank=len(fused) + 1,  # 새 순위
            metadata={**result.metadata, "rrf_score": rrf_score},
        ))

    return fused
```

---

## 5. 구현 우선순위 및 순서

### Phase 1: P2 마무리 (30분)

| Step | 작업 | 파일 |
|------|------|------|
| 1.1 | _schema.yaml backends 필드 추가 | `manifests/_schema.yaml` |
| 1.2 | dimension.aesthetic.yaml 예시 추가 | `manifests/dimension.aesthetic.yaml` |
| 1.3 | 테스트 실행 및 검증 | `pytest` |

### Phase 2: P3 Ensemble (2-3시간)

| Step | 작업 | 파일 |
|------|------|------|
| 2.1 | ensemble_retrieve() 함수 구현 | `hybrid_rag.py` |
| 2.2 | _weighted_rrf_fusion() 구현 | `hybrid_rag.py` |
| 2.3 | hybrid_query()에서 ensemble 호출 옵션 | `hybrid_rag.py` |
| 2.4 | 테스트 작성 | `tests/rag/test_ensemble.py` |
| 2.5 | 통합 테스트 및 벤치마크 | `pytest` |

### Phase 3: 문서화 및 최적화 (1시간)

| Step | 작업 | 파일 |
|------|------|------|
| 3.1 | CLAUDE.md RAG 섹션 업데이트 | `CLAUDE.md` |
| 3.2 | API 문서 추가 | `docs/` |
| 3.3 | 성능 프로파일링 | - |

---

## 6. 테스트 계획

### 6.1 단위 테스트 (test_ensemble.py)

```python
class TestEnsembleRetrieve:
    @pytest.mark.asyncio
    async def test_ensemble_with_all_backends(self):
        """전체 백엔드 ensemble 테스트."""
        results = await ensemble_retrieve(
            query="봉준호 스타일",
            app_key="dimension.aesthetic.direct",
        )
        assert len(results) > 0
        assert all(hasattr(r, "score") for r in results)

    @pytest.mark.asyncio
    async def test_ensemble_fallback_on_error(self):
        """백엔드 에러 시 fallback 테스트."""
        # Mock one backend to fail
        ...

    @pytest.mark.asyncio
    async def test_weighted_rrf_fusion(self):
        """RRF fusion 가중치 테스트."""
        ...


class TestWeightedRRFFusion:
    def test_fusion_basic(self):
        """기본 RRF fusion."""
        ...

    def test_fusion_with_overlap(self):
        """중복 문서 처리."""
        ...
```

### 6.2 통합 테스트

```bash
# 전체 RAG 테스트
cd backend && source venv/bin/activate
pytest tests/rag/ -v --tb=short

# 성능 벤치마크
pytest tests/rag/test_ensemble.py -v --benchmark-only
```

---

## 7. 의존성 및 호환성

### 7.1 기존 코드 영향

| 컴포넌트 | 영향 | 조치 |
|----------|------|------|
| `hybrid_query()` | 변경 없음 | 기존 호출 유지 |
| `tier1_dimension_rag` | 변경 없음 | Backend에서 래핑 |
| `tier0_notebooklm` | 변경 없음 | Backend에서 래핑 |
| `tier0_vertex_rag` | 변경 없음 | Backend에서 래핑 |
| `manifest_loader` | 이미 변경됨 | BackendConfig 추가 완료 |

### 7.2 Breaking Changes

**없음** - 모든 기존 API 호환 유지

### 7.3 새 기능 추가

| 함수/클래스 | 위치 | 설명 |
|-------------|------|------|
| `ensemble_retrieve()` | `hybrid_rag.py` | 병렬 Ensemble 검색 |
| `_weighted_rrf_fusion()` | `hybrid_rag.py` | RRF 결과 융합 |
| `BackendConfig` | `manifest_loader.py` | 백엔드 설정 (완료) |

---

## 8. 검증 체크리스트

### 8.1 P2 완료 조건 (✅ 완료)

- [x] `backends/base.py` - BaseBackend ABC 정의
- [x] `backends/__init__.py` - Auto-discovery Registry
- [x] `backends/qdrant_hybrid.py` - Qdrant 백엔드
- [x] `backends/notebooklm.py` - NotebookLM 백엔드
- [x] `backends/vertex_grounding.py` - Vertex 백엔드
- [x] `manifest_loader.py` - BackendConfig 추가
- [x] `tests/test_backend_registry.py` - Registry 테스트
- [x] `tests/test_backends.py` - 통합 테스트

### 8.2 P2 마무리 조건

- [ ] `_schema.yaml` - backends 필드 정의
- [ ] 앱별 YAML - backends 설정 예시

### 8.3 P3 완료 조건

- [ ] `ensemble_retrieve()` 구현
- [ ] `_weighted_rrf_fusion()` 구현
- [ ] `hybrid_query()` ensemble 옵션
- [ ] 테스트 통과 (신규 + 기존)
- [ ] 문서 업데이트

---

## 9. 리스크 및 완화

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| 병렬 실행 지연 | 전체 응답 지연 | timeout + graceful degradation |
| 백엔드 장애 | 부분 결과 | fallback to single backend |
| RRF 가중치 튜닝 | 검색 품질 | A/B 테스트 + 프리셋 기반 |
| 캐시 무효화 | 일관성 | ensemble 결과도 캐시 키에 포함 |

---

## 10. 참고 자료

### 10.1 Python Plugin Discovery Best Practices

- [Python Packaging - Creating and discovering plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
- `pkgutil.iter_modules()` - Internal plugin discovery
- `importlib.metadata.entry_points()` - External plugin discovery (Python 3.10+)

### 10.2 RRF (Reciprocal Rank Fusion)

- Original paper: Cormack et al. (2009)
- Formula: `score(d) = Σ 1/(k + rank(d))`, k=60
- Weighted variant: `score(d) = Σ w_i/(k + rank_i(d))`

### 10.3 관련 커밋

| Phase | 커밋 | 설명 |
|-------|------|------|
| P0 | `0128b669` | Qdrant Native Sparse 활성화 |
| P0.5 | `9af9f182` | Hybrid 컬렉션 마이그레이션 |
| P1 | `ad6250e6` | YAML Manifest 도입 |
| **P2** | `fa5f4499` | Backend ABC + Auto-discovery |
| P3 | (예정) | Ensemble Retriever |

---

## 11. 다음 단계

P2 마무리 후:

```bash
# 1. _schema.yaml 업데이트
# 2. 앱별 YAML backends 추가
# 3. 커밋

git add backend/app/rag/manifests/
git commit -m "feat(rag): P2 마무리 - YAML schema backends 필드 추가"

# 4. P3 구현 시작
```

---

**작성자**: Claude Opus 4.5
**최종 수정**: 2026-01-15
