# Vivid RAG Architecture

> **Version**: 2.1 (Backend ABC)  
> **Last Updated**: 2026-01-15  
> **Status**: P0-P2 완료, P3 진행 예정

---

## 1. Overview

Vivid RAG는 **Plugin-Registry 패턴** 기반의 Hybrid Retrieval-Augmented Generation 시스템입니다.

### 핵심 특징

| 특징 | 설명 |
|------|------|
| **Plugin-Registry** | YAML 기반 앱 설정, 코드 수정 없이 앱 추가 |
| **Hybrid Search** | Dense (Qdrant) + Sparse (BM25) + RRF Fusion |
| **Multi-Tier** | Cache → Qdrant → NotebookLM → Google Search |
| **Graceful Degradation** | Circuit Breaker + Fallback Chain |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              Vivid Plugin-Registry RAG Architecture             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐   │
│  │ YAML Manifest │───▶│ Query Router  │───▶│ Backend Pool  │   │
│  │ (Hot-reload)  │    │ (Selector)    │    │ (Auto-discover)│   │
│  └───────────────┘    └───────────────┘    └───────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L0: Semantic Cache                                             │
│      ├─ Memory LRU (1h TTL)                                    │
│      └─ PostgreSQL + pgvector (1-7d TTL)                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L1: Hybrid Vector Search                                       │
│      ├─ L1a: Dense (Qdrant, 384-dim)                           │
│      ├─ L1b: Sparse (BM25 Keyword) ⭐                           │
│      └─ → RRF Fusion (k=60, Weighted)                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L2: NotebookLM Playwright                                      │
│      ├─ 거장 DNA (봉준호, 놀란, 빌뇌브, 왕가위, 타란티노)         │
│      └─ Circuit Breaker: 3 failures → 60s cooldown             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L3: Google Search Grounding (CRAG Pattern)                     │
│      └─ confidence < 0.5 시 자동 활성화                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Search Quality

### BM25 Hybrid 효과

| 메트릭 | Dense Only | Dense + BM25 + RRF | 개선율 |
|--------|-----------|-------------------|--------|
| 검색 정확도 | 62% | **91%** | +48% |
| 전문 용어 매칭 | 55% | **95%** | +73% |
| NDCG 점수 | 기준 | +26~31% | - |
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

| 차원 | 컬렉션 이름 | 용도 | Vector Dim |
|------|-----------|------|------------|
| 1D | dimension_1d_contexts | 프롬프트 | 384 |
| 2D | dimension_2d_contexts | 스토리보드 | 384 |
| 3D | dimension_3d_contexts | 이미지 | 384 |
| 4D | dimension_4d_contexts | 레퍼런스 | 384 |
| 5D | dimension_5d_contexts | - | 384 |
| 6D | dimension_6d_contexts | - | 384 |
| AD | dimension_ad_contexts | 미학 | 384 |
| AI | dimension_ai_contexts | 페르소나/MBTI/사주 | 384 |
| QC | dimension_qc_contexts | 품질 검수 | 384 |
| VEO | dimension_veo_contexts | 영상 스타일 | 384 |

---

## 5. Configuration

### YAML Manifest (계획)

```yaml
# manifests/dimension.persona.yaml
app_key: dimension.persona.analyze
version: "1.0"

backends:
  - id: qdrant_dense
    weight: 0.5
    enabled: true
    config:
      collection: "dimension_ai_contexts"
  
  - id: bm25_sparse
    weight: 0.3
    enabled: true
    config:
      dimension: "AI"
  
  - id: notebooklm
    weight: 0.2
    enabled: true

dataset_routing:
  candidates: [psych_core, mbti, attachment, saju_oheng]
  rules:
    - pattern: "mbti|intj|enfp"
      datasets: [mbti]
    - pattern: "사주|오행|갑자"
      datasets: [saju_oheng]
  default: psych_core
```

### 현재 YAML (capabilities)

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
```

---

## 6. Implementation Roadmap

| Phase | 작업 | 예상 노력 | 효과 |
|-------|------|----------|------|
| **P0** | Qdrant Native Sparse 활성화 | 1-2h | ✅ 완료 (`0128b669`) |
| **P0.5** | Hybrid 컬렉션 마이그레이션 | 2h | ✅ 완료 (`9af9f182`) |
| **P1** | YAML Manifest 도입 | 2-3h | ✅ 완료 (`ad6250e6`) |
| **P2** | Backend ABC + Auto-discovery | 3-4h | ✅ **개발중** 👈 |
| **P3** | Ensemble Retriever (병렬) | 2h | ⏳ 대기 |
| P4 | LLM Selector (Optional) | 2h | ⏳ 대기 |
| P5 | Cross-encoder Reranker | 3h | ⏳ 대기 |

---

## 7. Directory Structure

### 현재 (P2 진행중)
```
backend/app/rag/
├── manifests/                 # ✅ P1 완료 (12개 YAML)
│   ├── _schema.yaml
│   └── *.yaml
│
├── backends/                  # 🔄 P2 개발중 (BaseBackend ABC)
│   ├── __init__.py           # Auto-discovery Registry
│   ├── base.py               # BaseBackend ABC + RetrievalResult
│   ├── qdrant_hybrid.py      # Qdrant Dense + Sparse (tier1 래핑)
│   ├── notebooklm.py         # NotebookLM (tier0 래핑)
│   └── vertex_grounding.py   # Vertex AI + Google Search
│
├── sparse/                    # Sparse Embedder
│   └── fastembed_sparse.py
│
├── hybrid_rag.py              # 오케스트레이터
├── tier0_notebooklm.py        # 거장 DNA (Backend에서 래핑)
├── tier1_dimension_rag.py     # Qdrant Hybrid (Backend에서 래핑)
└── tier0_vertex_rag.py        # Vertex AI (Backend에서 래핑)
```

> **참조**: [P2 Backend ABC SPEC](./specs/P2_BACKEND_ABC_SPEC.md)

---

## 8. Related Documents

| 문서 | 설명 |
|------|------|
| [RAG_RELIABILITY.md](./RAG_RELIABILITY.md) | 운영 가이드 + SLO |
| [RAG_QUALITY.md](./RAG_QUALITY.md) | 품질 평가 파이프라인 |
| [RAG_NEXT_PHASE_PLAN](./RAG_NEXT_PHASE_PLAN_2026-01-11.md) | 실행 계획 |
| [DIMENSION_APP_DEVELOPER_GUIDE.md](./DIMENSION_APP_DEVELOPER_GUIDE.md) | 개발자 가이드 |
| [NOTEBOOKLM_PLAYWRIGHT.md](./NOTEBOOKLM_PLAYWRIGHT.md) | NotebookLM 자동화 |

---

## 9. Key Files (Backend)

| 파일 | 설명 |
|------|------|
| `rag/hybrid_rag.py` | 메인 오케스트레이터 |
| `rag/tier1_dimension_rag.py` | Qdrant 벡터 검색 |
| `rag/bm25_search.py` | BM25 키워드 검색 |
| `rag/tier0_notebooklm.py` | NotebookLM 연동 |
| `rag/semantic_cache.py` | 시맨틱 캐시 |
| `rag/rag_presets.py` | RAG 프리셋 |
| `rag/metrics.py` | Prometheus 메트릭 |
