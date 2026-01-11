# RAG Reliability Guide

> **Status**: Production  
> **Last Updated**: 2026-01-11  
> **Based on**: 2025 RAG Best Practices Research

## Overview

Vivid의 Hybrid RAG 시스템 신뢰도 확보를 위한 가이드입니다.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ L0: Semantic Cache (pgvector + Memory LRU)                  │
│     Target: 30-50% cache hit rate                           │
├─────────────────────────────────────────────────────────────┤
│ L1: NotebookLM Playwright (거장 DNA)                         │
│     Circuit Breaker: 3 failures → 60s cooldown              │
├─────────────────────────────────────────────────────────────┤
│ L2: Vertex AI RAG (VDG + BM25/Vector RRF)                   │
├─────────────────────────────────────────────────────────────┤
│ L3: Google Search Grounding (실시간 정보)                    │
└─────────────────────────────────────────────────────────────┘
```

## Reliability Patterns

### 1. Circuit Breaker

NotebookLM RPC가 불안정할 때 빠른 실패 및 폴백:

```python
from circuitbreaker import circuit

@circuit(failure_threshold=3, recovery_timeout=60)
async def query_notebooklm(query: str, auteur_key: str):
    return await _playwright_query(query, auteur_key)
```

| State | 동작 |
|-------|------|
| Closed | 정상 요청 처리 |
| Open | 즉시 실패, Vertex AI 폴백 |
| Half-Open | 테스트 요청 허용 |

### 2. Multi-Layer Caching

| Layer | 저장소 | TTL | 용도 |
|-------|--------|-----|------|
| L1 | In-Memory LRU | 1h | Hot queries |
| L2 | PostgreSQL + pgvector | 1-7d | Persistent |

**pgvector 인덱스** (조회 10x 가속):
```sql
CREATE INDEX idx_semantic_cache_embedding 
ON rag_semantic_cache 
USING ivfflat (query_embedding vector_cosine_ops) 
WITH (lists = 100);
```

### 3. Fallback Chain

```
Query
  │
  ├─ L0: Cache Hit? → Return
  │
  ├─ L1: NotebookLM
  │      ├─ RPC 성공 → Return
  │      ├─ RPC 실패 → UI Fallback
  │      └─ Circuit Open → Skip
  │
  ├─ L2: Vertex AI RAG
  │      └─ BM25 + Vector RRF
  │
  └─ L3: Google Search (CRAG pattern)
         └─ confidence < 0.5 시 자동 활성화
```

## App RAG Configuration

### RAG Mode 선택 가이드

| Mode | 조건 | 예시 앱 |
|------|------|---------|
| `always` | 항상 RAG 필요 | AD, Story, QC |
| `auteur_only` | 거장 키 있을 때만 | 1D, 2D, 3D, VEO |
| `never` | RAG 불필요 | AI, Sound |

### YAML 설정

```yaml
capabilities:
  - name: rag
    enabled: true
    config:
      mode: auteur_only
      auteur_mode: true
      confidence_threshold: 0.7
      cache_ttl: 3600
      retrieval:
        strategy: hybrid  # hybrid | vector | keyword
        top_k: 10
        rrf_k: 60
```

## Monitoring

### Key Metrics

| Metric | Target | Alert |
|--------|--------|-------|
| Cache Hit Rate | 30-50% | < 20% |
| NotebookLM Latency | < 15s | > 30s |
| Circuit Open Events | 0/day | > 3/hour |

### Log Patterns

```bash
# 성공
[HybridRAG] SEMANTIC_CACHE HIT | query='...' | confidence=0.95
[NotebookLM-Playwright] Got answer via UI after 5s (250 chars)

# 폴백
[NotebookLM-Playwright] RPC query failed. Trying UI fallback...
[HybridRAG] NotebookLM circuit open, falling back to Vertex AI
```

## Related Files

- [hybrid_rag.py](file:///Users/ted/vivid/backend/app/rag/hybrid_rag.py)
- [tier0_notebooklm.py](file:///Users/ted/vivid/backend/app/rag/tier0_notebooklm.py)
- [semantic_cache.py](file:///Users/ted/vivid/backend/app/rag/semantic_cache.py)
- [notebooklm_playwright.py](file:///Users/ted/vivid/backend/app/rag/notebooklm_playwright.py)
