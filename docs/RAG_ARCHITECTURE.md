# Vivid RAG Architecture

<details open>
<summary>한국어</summary>

> **Version**: 3.0 (Multi-RAG Router)
> **Last Updated**: 2026-01-17
> **Status**: P0-P7 모두 완료 ✅

---

## 1. Overview

Vivid RAG는 **Multi-RAG Router 패턴** 기반의 Hybrid Retrieval-Augmented Generation 시스템입니다.

### 핵심 특징

| 특징 | 설명 |
|------|------|
| **Multi-RAG Router** | 쿼리 의도 분석 → 최적 백엔드 자동 라우팅 |
| **Plugin-Registry** | YAML 기반 앱 설정, 코드 수정 없이 앱 추가 |
| **Hybrid Search** | Dense (Qdrant Named Vectors) + Sparse (BM25 Native) + RRF Fusion |
| **Multi-Tier** | Cache → Qdrant → NotebookLM → Google Search |
| **Graceful Degradation** | Circuit Breaker + Fallback Chain |
| **Adaptive RAG** | Query Classification → 동적 전략 선택 |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Vivid Multi-RAG Router Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐           │
│   │    Query    │───▶│  Multi-RAG Router │───▶│  Backend Pool    │           │
│   │             │    │  (Intelligent)    │    │  (Auto-discover) │           │
│   └─────────────┘    └──────────────────┘    └──────────────────┘           │
│                              │                                               │
│                              ▼                                               │
│   ┌──────────────────────────────────────────────────────────────┐          │
│   │ Route Decision: NotebookLM | Qdrant | Hybrid | Skip          │          │
│   └──────────────────────────────────────────────────────────────┘          │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ L0: Semantic Cache (pgvector + Memory LRU + Redis)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ L1: Hybrid Vector Search                                                     │
│     ├─ Dense (Qdrant, 384-dim, Named Vectors)                               │
│     ├─ Sparse (BM25 Native) ⭐                                               │
│     └─ RRF Fusion (k=60, Weighted)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ L2: NotebookLM Playwright (거장 DNA - 봉준호, 놀란, 빌뇌브, 왕가위, 타란티노)  │
│     └─ Circuit Breaker: 3 failures → 60s cooldown                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ L3: Google Search Grounding (CRAG Pattern)                                   │
│     └─ confidence < 0.5 시 자동 활성화                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multi-RAG Router 로직

```python
# 쿼리 의도 → 라우팅 결정
def route_query(query: str, dimension: str) -> RouteDecision:
    if is_auteur_style_query(query):
        return RouteDecision.NOTEBOOKLM  # 거장 DNA
    elif is_technical_query(query):
        return RouteDecision.QDRANT_HYBRID  # 전문 용어 검색
    elif is_creative_query(query):
        return RouteDecision.HYBRID  # 둘 다 사용
    else:
        return RouteDecision.SKIP  # RAG 불필요
```

---

## 3. Search Quality

### BM25 Hybrid 효과

| 메트릭 | Dense Only | Dense + BM25 + RRF | 개선율 |
|--------|-----------|-------------------|--------|
| 검색 정확도 | 62% | **91%** | +48% |
| 전문 용어 매칭 | 55% | **95%** | +73% |
| NDCG 점수 | 기준 | +26~31% | ✅ |
| 환각 감소 | 기준 | 유의미 감소 | ✅ |

### RRF (Reciprocal Rank Fusion)

```
RRF_score(d) = Σ weight_i / (k + rank_i(d))

# 예시 (Dense 0.7, BM25 0.3, k=60):
문서 A: Dense rank=1, BM25 rank=5
W_RRF(A) = 0.7/(60+1) + 0.3/(60+5) = 0.0161
```

---

## 4. Qdrant Collections

### Named Vectors 구조 (P0.5 마이그레이션 완료)

| 차원 | 컬렉션 이름 | 용도 | Dense | Sparse |
|------|-----------|------|-------|--------|
| 1D | dimension_1d_contexts | 프롬프트 최적화 | 384 | ✅ |
| 2D | dimension_2d_contexts | 스토리보드 | 384 | ✅ |
| 3D | dimension_3d_contexts | 이미지 프롬프트 | 384 | ✅ |
| 4D | dimension_4d_contexts | 레퍼런스 분석 | 384 | ✅ |
| AD | dimension_ad_contexts | 미학 감독 | 384 | ✅ |
| AI | dimension_ai_contexts | 페르소나/MBTI/사주 | 384 | ✅ |
| QC | dimension_qc_contexts | 품질 검수 | 384 | ✅ |
| VEO | dimension_veo_contexts | 영상 스타일 | 384 | ✅ |
| Story | dimension_story_contexts | 시나리오 | 384 | ✅ |
| CC | dimension_cc_contexts | 캐릭터 일관성 | 384 | ✅ |

---

## 5. Configuration

### YAML Manifest (P1 완료)

```yaml
# manifests/dimension.persona.yaml
app_key: dimension.persona.analyze
version: "1.0"

backends:
  - id: qdrant_hybrid
    weight: 0.7
    enabled: true
    config:
      collection: "dimension_ai_contexts"
      use_sparse: true

  - id: notebooklm
    weight: 0.3
    enabled: true
    config:
      auteur_keys: ["bong", "nolan", "villeneuve"]

reranker:
  id: vertex
  enabled: true
  top_k: 5

routing:
  strategy: adaptive  # adaptive | always_hybrid | skip_notebooklm
  confidence_threshold: 0.7
```

### 현재 capabilities 설정

```yaml
capabilities:
  - name: rag
    enabled: true
    config:
      mode: auteur_only          # auteur_only | always | never
      confidence_threshold: 0.7
      cache_ttl: 3600
      retrieval:
        strategy: hybrid         # hybrid | vector | keyword
        top_k: 10
        rrf_k: 60
        bm25_weight: 0.3
        dense_weight: 0.7
      reranker:
        enabled: true
        model: vertex            # vertex | cross_encoder
        top_k: 5
```

---

## 6. Implementation Roadmap

| Phase | 작업 | 상태 |
|-------|------|------|
| **P0** | Qdrant Native Sparse 활성화 | ✅ 완료 |
| **P0.5** | Hybrid 컬렉션 마이그레이션 (Named Vectors) | ✅ 완료 |
| **P1** | YAML Manifest 도입 | ✅ 완료 |
| **P2** | Backend ABC + Auto-discovery | ✅ 완료 |
| **P3** | Ensemble Retriever (Weighted RRF) | ✅ 완료 |
| **P4** | Reranker Backend + Integration | ✅ 완료 |
| **P5** | Adaptive RAG (Query Classification) | ✅ 완료 |
| **P6** | Feedback Collection | ✅ 완료 |
| **P7** | Multi-RAG Router | ✅ 완료 |

---

## 7. Directory Structure

### 현재 (P7 완료)
```
backend/app/rag/
├── manifests/                 # ✅ P1 완료 (13개+ YAML)
│   ├── _schema.yaml           # YAML 스키마
│   └── *.yaml                 # 앱별 RAG 설정
│
├── backends/                  # ✅ P2 완료 (BaseBackend ABC)
│   ├── __init__.py           # Auto-discovery Registry
│   ├── base.py               # BaseBackend ABC + RetrievalResult
│   ├── qdrant_hybrid.py      # Qdrant Dense + Sparse (Named Vectors)
│   ├── notebooklm.py         # NotebookLM Playwright
│   └── vertex_grounding.py   # Vertex AI + Google Search
│
├── rerankers/                 # ✅ P4 완료 (BaseReranker ABC)
│   ├── __init__.py           # Auto-discovery Registry
│   ├── base.py               # BaseReranker ABC + RerankResult
│   ├── vertex.py             # Vertex AI Ranking API
│   └── cross_encoder.py      # Local BGE/ms-marco CrossEncoder
│
├── router/                    # ✅ P7 완료 (Multi-RAG Router)
│   ├── __init__.py
│   ├── query_classifier.py   # 쿼리 의도 분류
│   └── route_selector.py     # 라우팅 결정
│
├── feedback/                  # ✅ P6 완료 (Feedback Collection)
│   ├── __init__.py
│   └── collector.py          # 피드백 수집 + 분석
│
├── sparse/                    # Sparse Embedder
│   └── fastembed_sparse.py
│
├── hybrid_rag.py              # 메인 오케스트레이터
├── manifest_loader.py         # YAML Manifest Loader
├── tier0_notebooklm.py        # 거장 DNA
├── tier1_dimension_rag.py     # Qdrant Hybrid
├── tier0_vertex_rag.py        # Vertex AI
├── semantic_cache.py          # L0 캐시
├── rag_presets.py             # 거장 스타일 힌트
└── metrics.py                 # Prometheus 메트릭
```

---

## 8. Related Documents

| 문서 | 설명 |
|------|------|
| [RAG_RELIABILITY.md](./RAG_RELIABILITY.md) | 운영 가이드 + SLO |
| [DIMENSION_APP_DEVELOPER_GUIDE.md](./DIMENSION_APP_DEVELOPER_GUIDE.md) | 개발자 가이드 |
| [NOTEBOOKLM_PLAYWRIGHT.md](./NOTEBOOKLM_PLAYWRIGHT.md) | NotebookLM 자동화 |

> **Archived**: P2/P3 SPEC 문서는 `docs/archive/specs/`로 이동됨

---

## 9. Key Files (Backend)

| 파일 | 설명 |
|------|------|
| `rag/hybrid_rag.py` | 메인 오케스트레이터 (ensemble_retrieve, hybrid_query) |
| `rag/router/query_classifier.py` | P5 쿼리 분류기 |
| `rag/router/route_selector.py` | P7 라우팅 결정 |
| `rag/manifest_loader.py` | YAML Manifest Loader |
| `rag/backends/__init__.py` | Backend Registry |
| `rag/rerankers/__init__.py` | Reranker Registry |
| `rag/feedback/collector.py` | P6 피드백 수집 |
| `rag/tier1_dimension_rag.py` | Qdrant 벡터 검색 |
| `rag/tier0_notebooklm.py` | NotebookLM 연동 |
| `rag/semantic_cache.py` | 시맨틱 캐시 |

</details>

<details>
<summary>English</summary>

> **Version**: 3.0 (Multi-RAG Router)
> **Last Updated**: 2026-01-17
> **Status**: P0-P7 All Complete ✅

---

## 1. Overview

Vivid RAG is a hybrid retrieval-augmented generation system based on the **Multi-RAG Router** pattern.

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-RAG Router** | Query intent analysis → Automatic optimal backend routing |
| **Plugin-Registry** | YAML-based app config; add apps without code changes |
| **Hybrid Search** | Dense (Qdrant Named Vectors) + Sparse (BM25 Native) + RRF Fusion |
| **Multi-Tier** | Cache → Qdrant → NotebookLM → Google Search |
| **Graceful Degradation** | Circuit Breaker + Fallback Chain |
| **Adaptive RAG** | Query Classification → Dynamic strategy selection |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Vivid Multi-RAG Router Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐           │
│   │    Query    │───▶│  Multi-RAG Router │───▶│  Backend Pool    │           │
│   │             │    │  (Intelligent)    │    │  (Auto-discover) │           │
│   └─────────────┘    └──────────────────┘    └──────────────────┘           │
│                              │                                               │
│                              ▼                                               │
│   ┌──────────────────────────────────────────────────────────────┐          │
│   │ Route Decision: NotebookLM | Qdrant | Hybrid | Skip          │          │
│   └──────────────────────────────────────────────────────────────┘          │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ L0: Semantic Cache (pgvector + Memory LRU + Redis)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ L1: Hybrid Vector Search                                                     │
│     ├─ Dense (Qdrant, 384-dim, Named Vectors)                               │
│     ├─ Sparse (BM25 Native) ⭐                                               │
│     └─ RRF Fusion (k=60, Weighted)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ L2: NotebookLM Playwright (Auteur DNA - Bong, Nolan, Villeneuve, WKW, QT)   │
│     └─ Circuit Breaker: 3 failures → 60s cooldown                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ L3: Google Search Grounding (CRAG Pattern)                                   │
│     └─ Auto-enabled when confidence < 0.5                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multi-RAG Router Logic

```python
# Query intent → Routing decision
def route_query(query: str, dimension: str) -> RouteDecision:
    if is_auteur_style_query(query):
        return RouteDecision.NOTEBOOKLM  # Auteur DNA
    elif is_technical_query(query):
        return RouteDecision.QDRANT_HYBRID  # Technical term search
    elif is_creative_query(query):
        return RouteDecision.HYBRID  # Use both
    else:
        return RouteDecision.SKIP  # RAG not needed
```

---

## 3. Search Quality

### BM25 Hybrid Impact

| Metric | Dense Only | Dense + BM25 + RRF | Improvement |
|--------|-----------|-------------------|-------------|
| Search accuracy | 62% | **91%** | +48% |
| Domain term match | 55% | **95%** | +73% |
| NDCG score | baseline | +26~31% | ✅ |
| Hallucination reduction | baseline | meaningful drop | ✅ |

### RRF (Reciprocal Rank Fusion)

```
RRF_score(d) = Σ weight_i / (k + rank_i(d))

# Example (Dense 0.7, BM25 0.3, k=60):
Doc A: Dense rank=1, BM25 rank=5
W_RRF(A) = 0.7/(60+1) + 0.3/(60+5) = 0.0161
```

---

## 4. Qdrant Collections

### Named Vectors Structure (P0.5 Migration Complete)

| Dimension | Collection | Use | Dense | Sparse |
|-----------|-----------|-----|-------|--------|
| 1D | dimension_1d_contexts | Prompt optimization | 384 | ✅ |
| 2D | dimension_2d_contexts | Storyboard | 384 | ✅ |
| 3D | dimension_3d_contexts | Image prompts | 384 | ✅ |
| 4D | dimension_4d_contexts | Reference analysis | 384 | ✅ |
| AD | dimension_ad_contexts | Aesthetics | 384 | ✅ |
| AI | dimension_ai_contexts | Persona/MBTI/Saju | 384 | ✅ |
| QC | dimension_qc_contexts | Quality review | 384 | ✅ |
| VEO | dimension_veo_contexts | Video style | 384 | ✅ |
| Story | dimension_story_contexts | Scenario | 384 | ✅ |
| CC | dimension_cc_contexts | Character consistency | 384 | ✅ |

---

## 5. Configuration

### YAML Manifest (P1 Complete)

```yaml
# manifests/dimension.persona.yaml
app_key: dimension.persona.analyze
version: "1.0"

backends:
  - id: qdrant_hybrid
    weight: 0.7
    enabled: true
    config:
      collection: "dimension_ai_contexts"
      use_sparse: true

  - id: notebooklm
    weight: 0.3
    enabled: true
    config:
      auteur_keys: ["bong", "nolan", "villeneuve"]

reranker:
  id: vertex
  enabled: true
  top_k: 5

routing:
  strategy: adaptive  # adaptive | always_hybrid | skip_notebooklm
  confidence_threshold: 0.7
```

### Current Capabilities Config

```yaml
capabilities:
  - name: rag
    enabled: true
    config:
      mode: auteur_only          # auteur_only | always | never
      confidence_threshold: 0.7
      cache_ttl: 3600
      retrieval:
        strategy: hybrid         # hybrid | vector | keyword
        top_k: 10
        rrf_k: 60
        bm25_weight: 0.3
        dense_weight: 0.7
      reranker:
        enabled: true
        model: vertex            # vertex | cross_encoder
        top_k: 5
```

---

## 6. Implementation Roadmap

| Phase | Work | Status |
|-------|------|--------|
| **P0** | Enable Qdrant Native Sparse | ✅ Complete |
| **P0.5** | Hybrid collection migration (Named Vectors) | ✅ Complete |
| **P1** | YAML Manifest adoption | ✅ Complete |
| **P2** | Backend ABC + Auto-discovery | ✅ Complete |
| **P3** | Ensemble Retriever (Weighted RRF) | ✅ Complete |
| **P4** | Reranker Backend + Integration | ✅ Complete |
| **P5** | Adaptive RAG (Query Classification) | ✅ Complete |
| **P6** | Feedback Collection | ✅ Complete |
| **P7** | Multi-RAG Router | ✅ Complete |

---

## 7. Directory Structure

### Current (P7 Complete)
```
backend/app/rag/
├── manifests/                 # ✅ P1 done (13+ YAML)
│   ├── _schema.yaml           # YAML schema
│   └── *.yaml                 # Per-app RAG configs
│
├── backends/                  # ✅ P2 done (BaseBackend ABC)
│   ├── __init__.py           # Auto-discovery Registry
│   ├── base.py               # BaseBackend ABC + RetrievalResult
│   ├── qdrant_hybrid.py      # Qdrant Dense + Sparse (Named Vectors)
│   ├── notebooklm.py         # NotebookLM Playwright
│   └── vertex_grounding.py   # Vertex AI + Google Search
│
├── rerankers/                 # ✅ P4 done (BaseReranker ABC)
│   ├── __init__.py           # Auto-discovery Registry
│   ├── base.py               # BaseReranker ABC + RerankResult
│   ├── vertex.py             # Vertex AI Ranking API
│   └── cross_encoder.py      # Local BGE/ms-marco CrossEncoder
│
├── router/                    # ✅ P7 done (Multi-RAG Router)
│   ├── __init__.py
│   ├── query_classifier.py   # Query intent classification
│   └── route_selector.py     # Routing decision
│
├── feedback/                  # ✅ P6 done (Feedback Collection)
│   ├── __init__.py
│   └── collector.py          # Feedback collection + analysis
│
├── sparse/                    # Sparse Embedder
│   └── fastembed_sparse.py
│
├── hybrid_rag.py              # Main orchestrator
├── manifest_loader.py         # YAML Manifest Loader
├── tier0_notebooklm.py        # Auteur DNA
├── tier1_dimension_rag.py     # Qdrant Hybrid
├── tier0_vertex_rag.py        # Vertex AI
├── semantic_cache.py          # L0 cache
├── rag_presets.py             # Auteur style hints
└── metrics.py                 # Prometheus metrics
```

---

## 8. Related Documents

| Document | Description |
|----------|-------------|
| [RAG_RELIABILITY.md](./RAG_RELIABILITY.md) | Operations guide + SLO |
| [DIMENSION_APP_DEVELOPER_GUIDE.md](./DIMENSION_APP_DEVELOPER_GUIDE.md) | Developer guide |
| [NOTEBOOKLM_PLAYWRIGHT.md](./NOTEBOOKLM_PLAYWRIGHT.md) | NotebookLM automation |

> **Archived**: P2/P3 SPEC docs moved to `docs/archive/specs/`

---

## 9. Key Files (Backend)

| File | Description |
|------|-------------|
| `rag/hybrid_rag.py` | Main orchestrator (ensemble_retrieve, hybrid_query) |
| `rag/router/query_classifier.py` | P5 Query classifier |
| `rag/router/route_selector.py` | P7 Routing decision |
| `rag/manifest_loader.py` | YAML Manifest Loader |
| `rag/backends/__init__.py` | Backend Registry |
| `rag/rerankers/__init__.py` | Reranker Registry |
| `rag/feedback/collector.py` | P6 Feedback collection |
| `rag/tier1_dimension_rag.py` | Qdrant vector search |
| `rag/tier0_notebooklm.py` | NotebookLM integration |
| `rag/semantic_cache.py` | Semantic cache |

</details>
